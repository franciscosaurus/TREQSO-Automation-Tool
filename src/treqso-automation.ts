/**
 * TREQSO Automation Tool - TypeScript/Playwright Core
 * Handles browser automation for TREQSO part and BOM management
 */

import { chromium, Browser, Page, BrowserContext } from '@playwright/test';

export interface Part {
  partNumber: string;
  partDescription: string;
  fullDescription?: string;
  partCategory: string;
  productCode: string;
  salesGroup?: string;
  partType: string;
  phaseNumber?: string;
  orderType?: string;
  standardCost?: string;
  unitOfMeasure: string;
  defaultCostField: string;
}

/**
 * Represents a partial update to an existing part.
 * partNumber is required to locate the record; all other fields are optional.
 * Only fields that are present and non-empty in the CSV will be written to TREQSO.
 */
export interface PartUpdate {
  partNumber: string;
  partStatus?: string;
  partDescription?: string;
  fullDescription?: string;
  partCategory?: string;
  productCode?: string;
  salesGroup?: string;
  partType?: string;
  phaseNumber?: string;
  standardCost?: string;
  unitOfMeasure?: string;
  defaultCostField?: string;
}

export interface BOMLine {
  BOMSequence: string;
  BOMOption?: string;
  partNumber: string;
  unitOfMeasure: string;
  quantity: string;
}

export interface TREQSOConfig {
  url: string;
  company: string;
  headless?: boolean;
  slowMo?: number;
}

export class TREQSOAutomation {
  private browser: Browser | null = null;
  private context: BrowserContext | null = null;
  private page: Page | null = null;
  private config: TREQSOConfig;

  constructor(config: TREQSOConfig) {
    this.config = {
      headless: false,
      slowMo: 0,
      ...config
    };
  }

  /**
   * Start the browser and create a new page
   */
  async startBrowser(): Promise<void> {
    console.log('Starting browser...');
    this.browser = await chromium.launch({
      headless: this.config.headless,
      slowMo: this.config.slowMo,
      args: [
      '--kiosk-printing', // Auto-print without dialog
      ]
    });
    
    this.context = await this.browser.newContext();
    this.page = await this.context.newPage();
    this.page.setDefaultTimeout(60000);
    
    console.log('Browser started successfully');
  }

  /**
   * Log into TREQSO
   */
  async login(): Promise<void> {
    if (!this.page) throw new Error('Browser not started');

    console.log(`Navigating to TREQSO: ${this.config.url}`);
    await this.page.goto(this.config.url);

    const submitSelector = this.page.getByRole('button', { name: 'Login' });
   
    await this.page.locator('#rbWindows').check();
    await submitSelector.click();

    // Wait for login to complete
    await this.page.waitForLoadState('networkidle');
    console.log('Login successful!');

    // Verify Company
    const texts = await this.page.getByText('Company:').allInnerTexts();

    if (!texts[0].startsWith('Company: ' + this.config.company + '  User:')) {
      await this.page.getByRole('button', { name: 'Switch Company' }).click();
      await this.page.locator('#ddlDatabases_Input').click();
      await this.page.getByText(this.config.company, {exact: true}).click();
      await this.page.getByRole('button', { name: 'Login' }).click();
    }
  }
  
  async WaitToLoad(): Promise<void> {
    if (!this.page) throw new Error('Browser not started');
    await this.page.waitForTimeout(1250);
    await this.page.getByAltText('Loading...').waitFor({state: 'hidden'})
  }

  /**
   * Print all MOs within a parent MO
   */
  async printMOs(referenceID: string): Promise<Record<string, boolean>> {
    if (!this.page) throw new Error('Browser not started');
    const results: Record<string, boolean> = {};
    
    try {
      const manufacturingOrderIDs = await this.navigateAndProcessMOs(referenceID);

      for (let MO_ID of manufacturingOrderIDs) {
        try {
          //Searching and editing the ASM#
          console.log(` Navigating to MO for ${MO_ID}`);

          // Going to MO Maintenance page
          await this.page.goto(this.config.url + '/MFG/MfgOrderMaint.aspx');

          // Filter by MO ID
          await this.page.getByAltText('Filter Mfg Order ID column').fill(MO_ID);
          await this.page.getByAltText('Filter Mfg Order ID column').press('Enter');
          await this.WaitToLoad();

          // Open MO
          await this.page.getByTitle('Select').click();
          await this.WaitToLoad();

          // Print MO
          await this.page.getByRole('link', { name: 'Print Order' }).click();
          const printPopUp = this.page.waitForEvent('popup');
          await this.page.locator('iframe[name="winPrintOrder"]').contentFrame().getByRole('button', { name: 'Print', exact: true }).click();
          const pagePrint = await printPopUp;
          await pagePrint.waitForLoadState('networkidle')

          await pagePrint.evaluate(() => window.print());
          console.log(` Successfully printed MO: ${MO_ID}`);
          results[MO_ID] = true;
        } catch (moError) {
          console.error(`Failed to print MO ${MO_ID}:`, moError);
          await this.takeScreenshot(`error_print_MO_${MO_ID}.png`);
          results[MO_ID] = false;
        }
      }
      
      return results;

    } catch (error) {
      console.error(`Error printing MOs for ${referenceID}:`, error);
      await this.takeScreenshot(`error_print_MOs_${referenceID}.png`);
      return results;
    }
  }

  /**
   * Navigate to the BOM for a specific part/assembly
   */
  async navigateAndProcessMOs(referenceID: string): Promise<string[]> {
    if (!this.page) throw new Error('Browser not started'); 
    
    await this.page.goto(this.config.url + '/MFG/MfgOrderMaint.aspx');

    await this.page.getByAltText('Filter Order Status column').fill('Open');
    await this.page.getByAltText('Filter Order Status column').press('Enter');
    await this.WaitToLoad();
    await this.page.getByAltText('Filter Order Reference ID').fill(referenceID);
    await this.page.getByAltText('Filter Order Reference ID').press('Enter');
    await this.WaitToLoad();

    let MOs: string[] = [];

      const table = this.page.locator('#ctl00_ContentPlaceHolder1_Finder1_gridFinder_ctl00');
      let rows = table.locator('tbody').getByRole('row')
        .filter({has: this.page.getByTitle('Select')});

      // Get the count of rows
      const rowCount = await rows.count() ?? 0

      // Get the number of pages
      let pages = 1
      const innerText = (await this.page.getByText('records found').allInnerTexts())[0]
      if (innerText){pages = Math.ceil(+innerText.slice(1, 4) / 20)}
      
      if (pages == 1){
        for (let i = 0; i < rowCount; i++){
          const row = rows.nth(i);
          
          // Get all cells in the row
          const cells = row.locator('td');
          const cellCount = await cells.count() ?? 0;
          
          // Extract assembly part number
          if (cellCount > 0) {
            const assemblyNumber = await cells.nth(1).textContent();
            if (assemblyNumber) {
              MOs.push(assemblyNumber.trim());
            }
          }
        }
      } else {
        for (let j = 0; j < pages; j++){
          if (j != 0) {
            await this.page.getByRole('button', { name: '>', exact: true }).click();
            await this.WaitToLoad();
            rows = table.locator('tbody').getByRole('row')
              .filter({has: this.page.getByTitle('Select')});
          }
          for (let i = 0; i < rowCount; i++){
            const row = rows.nth(i);
            
            // Get all cells in the row
            const cells = row.locator('td');
            const cellCount = await cells.count() ?? 0;
            
            // Extract assembly part number
            if (cellCount > 0) {
              const assemblyNumber = await cells.nth(1).textContent();
              if (assemblyNumber) {
                MOs.push(assemblyNumber.trim());
              }
            }
          }
        
      }
    }
    return MOs;
  }

  /**
   * Navigate to the Add Parts module
   */
  async navigateToAddParts(): Promise<void> {
    if (!this.page) throw new Error('Browser not started');
    
    console.log(' Navigating to Parts module...');
    await this.page.goto(this.config.url + '/IMS/PartMaint.aspx?IsNew=Yes');
  }

  /**
   * Create a new part in TREQSO
   */
  async createPart(part: Part, save: boolean = true): Promise<boolean> {
    if (!this.page) throw new Error('Browser not started');

    try {
      console.log(`Creating part: ${part.partNumber}`);

      this.navigateToAddParts();

      // Wait for form to load
      await this.page.waitForLoadState('networkidle');

      // Fill in Part Number
      if (part.partNumber) {
        await this.page.locator('#ContentPlaceHolder1_txtPartNumber').fill(part.partNumber);
      }

      // Fill in Part Description
      if (part.partDescription) {
        await this.page.locator('#ContentPlaceHolder1_txtPartDescription').fill(part.partDescription);
      }

      // Fill in Full Description
      if (part.fullDescription) {
        await this.page.locator('#ContentPlaceHolder1_txtPlainFullDescription').fill(part.fullDescription);
      }

      // Fill in Part Category
      if (part.partCategory) {
        await this.page.locator('#ctl00_ContentPlaceHolder1_ddlPartCategory_Input').fill(part.partCategory);
      }

      // Fill in Product Code
      if (part.productCode) {
        await this.page.locator('#ctl00_ContentPlaceHolder1_ddlProductCode_Input').fill(part.productCode);
      }

      // Fill in Sales Group
      if (part.salesGroup) {
        await this.page.locator('#ctl00_ContentPlaceHolder1_ddlSalesGroup_Input').fill(part.salesGroup);
      }

      // Fill in Part Type
      if (part.partType) {
        await this.page.locator('#ctl00_ContentPlaceHolder1_ddlPartType_Input').fill(part.partType);
      }

      // Fill in Phase Number
      if (part.phaseNumber) {
        await this.page.locator('#ctl00_ContentPlaceHolder1_ddlPhaseNumber_Input').fill(part.phaseNumber);
      } else {
        await this.page.locator('#ctl00_ContentPlaceHolder1_ddlPhaseNumber_Input').fill('110 (Parts)');
      }

      // Fill in Order Type
      if (part.orderType) {
        await this.page.locator('#ctl00_ContentPlaceHolder1_ddlOrderType_Input').fill(part.orderType);
      }

      // Fill in Unit of Measure
      if (part.unitOfMeasure) {
        await this.page.locator('#ctl00_ContentPlaceHolder1_ddlUOM1_Input').fill(part.unitOfMeasure);
      }

      // Fill in Standard Cost
      if (part.standardCost) {
        await this.page.locator('#ctl00_ContentPlaceHolder1_numStandardCost').fill(part.standardCost);
      }

      // Fill in Default Cost Field
      if (part.defaultCostField) {
        await this.page.locator('#ctl00_ContentPlaceHolder1_ddlDefaultCostField_Input').fill(part.defaultCostField);
      }

      // Save the part if requested
      if (save) {
        const saveButton = this.page.getByRole('button', { name: 'Add', exact: true });
        await saveButton.click();

        // Wait for save confirmation
        await this.WaitToLoad();
        console.log(` Part ${part.partNumber} created successfully!`);
      }

      return true;

    } catch (error) {
      console.error(`Error creating part ${part.partNumber}:`, error);
      await this.takeScreenshot(`error_create_part_${part.partNumber}.png`);
      return false;
    }
  }

  /**
   * Navigate to the BOM for a specific part/assembly
   */
  async navigateToBOM(partNumber: string, firstPart?: BOMLine, component?: boolean): Promise<void> {
    if (!this.page) throw new Error('Browser not started'); 

    await this.page.goto(this.config.url + '/MFG/BillOfMaterialsMaint.aspx');

    if (firstPart) {
      console.log(` Navigating to create BOM for ${partNumber}`);
      await this.page.getByRole('button', { name: 'Add BOM' }).click();
      
      if(firstPart.BOMOption){
        await this.page.locator('#ctl00_ContentPlaceHolder1_txtBOMOptionNumber').fill(firstPart.BOMOption);
      }
      // Inputing ASM#
      await this.page.locator('#ctl00_ContentPlaceHolder1_txtParentPart_Input').click();
      await this.page.locator('#ctl00_ContentPlaceHolder1_txtParentPart_Input').pressSequentially(partNumber);
      await this.page.waitForTimeout(1250);

      // Inputing First Component PRT#
      await this.page.locator('#ctl00_ContentPlaceHolder1_txtComponentPart_Input').pressSequentially(firstPart.partNumber);
      await this.page.waitForTimeout(1250);

      // Inputting Quantity
      await this.page.locator('#ctl00_ContentPlaceHolder1_txtQuantity').fill(firstPart.quantity.toString());

      // Unchecking is Assembly?
      await this.page.waitForTimeout(1250);
      await this.page.getByRole('checkbox').first().click({ force: true });

      // Creating the assembly with the first part
      await this.page.getByRole('button', { name: 'Add' }).click()

      // Allow the BOM to load before adding more lines
      await this.WaitToLoad();
    } else if (!component){
      //Searching and editting the ASM#
      console.log(` Navigating to BOM for ${partNumber}`);

      await this.page.getByAltText('Filter ParentPartNumber column').fill(partNumber);
      await this.page.getByAltText('Filter ParentPartNumber column').press('Enter');
      await this.WaitToLoad();
      await this.page.locator('#ctl00_ContentPlaceHolder1_gridFinder1_ctl00_ctl04_gbcSelectRecord').click();
      await this.WaitToLoad();
    } else {
      console.log(` Navigating to Parent BOMs for ${partNumber}`);

      await this.page.getByRole('button', {name: 'Detail Finder'}).click()
      await this.WaitToLoad();
      await this.page.getByAltText('Filter ComponentPartNumber column').fill(partNumber);
      await this.page.getByAltText('Filter ComponentPartNumber column').press('Enter');
      await this.WaitToLoad();
      await this.page.locator('#ctl00_ContentPlaceHolder1_gridFinder2_ctl00_ctl02_ctl03_Filter_ComponentPartNumber').click();
      await this.WaitToLoad();
      await this.page.getByText('EqualTo', {exact: true }).click();
      await this.WaitToLoad();
    }
  }

  /**
   * Create and fill multiple BOMs
   */
  async createBOM(BOMs: any): Promise<boolean> {
    if (!this.page) throw new Error('Browser not started');

    try {
      console.log(`Creating ${Object.keys(BOMs).length} BOMs`);

      // Iterate through all the BOMs
      for (const key of Object.keys(BOMs)) {
        const asmNumber: string = BOMs[key].assemblyPartNumber
        const parts: BOMLine[] = BOMs[key].bomLines
        let firstPart: BOMLine = parts[0]

        console.log(` Creating BOM for ${asmNumber}`)
        await this.navigateToBOM(asmNumber, firstPart);
        
        // Add each line to the BOM
        for (const line of parts) {
          if (line != firstPart){

            // Clicking Add Detail
            console.log(`  Adding line ${line.BOMSequence}: ${line.partNumber} (Qty: ${line.quantity})`);
            await this.page.getByRole('button', { name: 'Add Detail' }).click();
            await this.WaitToLoad();

            // Inputting BOM Sequence
            await this.page.locator('#ctl00_ContentPlaceHolder1_txtBOMSequenceNumber').fill(line.BOMSequence);

            // Inputting BOM Option
            if(line.BOMOption){
              await this.page.locator('#ctl00_ContentPlaceHolder1_txtBOMOptionNumber').fill(line.BOMOption);
            }

            // Inputting Component PRT#
            await this.page.locator('#ctl00_ContentPlaceHolder1_txtComponentPart_Input').pressSequentially(line.partNumber);
            await this.page.waitForTimeout(1250);

            // Inputting Quantity
            await this.page.locator('#ctl00_ContentPlaceHolder1_txtQuantity').fill(line.quantity.toString());
            
            // Unchecking is Assembly?
            await this.page.waitForTimeout(1250);
            await this.page.getByRole('checkbox').first().click({ force: true });

            // Saving Detail
            await this.page.getByRole('button', { name: 'Save' }).click();

            await this.WaitToLoad();
          }
        }
        console.log(` BOM for ${asmNumber} created and filled successfully!`);
      }

      console.log(`${Object.keys(BOMs).length} BOMs created and filled successfully`);
      return true;

    } catch (error) {
      console.error(`Error creating BOM for ${BOMs}:`, error);
      await this.takeScreenshot(`error_create_bom_${BOMs}.png`);
      return false;
    }
  }

  /**
   * Find all assemblies the old part number is in
   */
  async processAssemblyNumbers(
    oldPartNumber: string,
  ): Promise<string[]> {
    if (!this.page) throw new Error('Browser not started');

    try {
      let assemblies: string[] = [];

      await this.navigateToBOM(oldPartNumber, undefined, true);

      const table = this.page.locator('#ctl00_ContentPlaceHolder1_gridFinder2_ctl00');
      let rows = table.locator('tbody').getByRole('row').filter({has: this.page.getByAltText('Edit Record')});

      // Get the count of rows
      const rowCount = await rows.count() ?? 0

      // Get the number of pages
      let pages = 1
      const innerText = (await this.page.getByText('items in').allInnerTexts())[0]
      if (innerText){pages = +innerText.slice(-8, -6)}
      
      // console.log('Inner Text: ' + innerText);
      // console.log('Pages: ' + pages);
      if (pages == 1){
        for (let i = 0; i < rowCount; i++){
          const row = rows.nth(i);
          
          // Get all cells in the row
          const cells = row.locator('td');
          const cellCount = await cells.count() ?? 0;
          
          // Extract assembly part number
          if (cellCount > 0) {
            const assemblyNumber = await cells.nth(1).textContent();
            if (assemblyNumber) {
              assemblies.push(assemblyNumber.trim());
            }
          }
        }
      } else {
        for (let j = 0; j < pages; j++){
          if (j != 0) {
            await this.page.getByTitle('Next Page', { exact: true }).click();
            await this.WaitToLoad();
            rows = table.locator('tbody').getByRole('row')
              .filter({has: this.page?.getByAltText('Edit Record')});
          }
          for (let i = 0; i < rowCount; i++){
            const row = rows.nth(i);
            
            // Get all cells in the row
            const cells = row.locator('td');
            const cellCount = await cells.count() ?? 0;
            
            // Extract assembly part number
            if (cellCount > 0) {
              const assemblyNumber = await cells.nth(1).textContent();
              if (assemblyNumber) {
                assemblies.push(assemblyNumber.trim());
              }
            }
          }
          
        }
      }

      console.log(`${assemblies.length} assemblies found containing ${oldPartNumber}`);
      return assemblies;
    } catch (error) {
      console.error(`Error processing parent part numbers:`, error);
      await this.takeScreenshot(`error_replace_bom_${oldPartNumber}.png`);
      return [(`Error processing parent part numbers:` + error)];
    }
  }

  /**
   * Replace a part in a BOM with a different part
   */
  async massReplaceBOMParts(
    oldPartNumber: string,
    newPartNumber: string,
    updateQuantity?: string
  ): Promise<boolean> {
    if (!this.page) throw new Error('Browser not started');
    
    const ASMs: string[] = await this.processAssemblyNumbers(oldPartNumber)
    try {

      for(const ASM of ASMs){
        console.log(`Replacing ${oldPartNumber} with ${newPartNumber} in ${ASM}`);
        
        // Navigate to the BOM
        await this.navigateToBOM(ASM);

        // Set page size to All
        const pageSizeBox =  this.page.locator('#ctl00_ContentPlaceHolder1_rgDetail_ctl00_ctl03_ctl02_PageSizeComboBox').getByRole('cell', { name: '10' });
        if (await pageSizeBox.isVisible()) {
          await pageSizeBox.click();
          await this.page.getByText('All', { exact: true }).click();
          await this.WaitToLoad();
        }
        
        // Find and select the row with the old part number
        const table = this.page.locator('#ctl00_ContentPlaceHolder1_rgDetail_ctl00');
        let oldPartRow = table.locator('tbody').getByRole('row')
          .filter({hasText: oldPartNumber}).locator('td');

        // Get BOM sequence number
        let BOMSeqNumber = await oldPartRow.nth(3).textContent();
        let BOMOptionNumber = await oldPartRow.nth(4).textContent();
        let quantity = await oldPartRow.nth(8).textContent();

        // Press edit detail
        await oldPartRow.getByAltText('Edit Detail').click()
        await this.WaitToLoad();

        // Delete the old part number detail
        this.page.once('dialog', dialog => {
          // console.log(`Dialog message: ${dialog.message()}`);
          dialog.accept();
          console.log(` Deleting ${oldPartNumber} detail`);
        });
        await this.page.getByRole('button', {name: 'Delete'}).click();
        await this.WaitToLoad();

        // Clicking Add Detail
        await this.page.getByRole('button', { name: 'Add Detail' }).click();
        await this.WaitToLoad();
        console.log(` Adding ${newPartNumber} detail`);

        // Inputting BOM Sequence
        if(BOMSeqNumber){
          await this.page.locator('#ctl00_ContentPlaceHolder1_txtBOMSequenceNumber').fill(BOMSeqNumber);
        }

        // Inputting BOM Option
        if(BOMOptionNumber){
          await this.page.locator('#ctl00_ContentPlaceHolder1_txtBOMOptionNumber').fill(BOMOptionNumber);
        }

        // Inputting Component PRT#
        await this.page.locator('#ctl00_ContentPlaceHolder1_txtComponentPart_Input').pressSequentially(newPartNumber);
        await this.page.waitForTimeout(1250);

        // Inputting Quantity
        if(updateQuantity) {
          await this.page.locator('#ctl00_ContentPlaceHolder1_txtQuantity').fill(updateQuantity.toString());
        } else if(quantity) {
          await this.page.locator('#ctl00_ContentPlaceHolder1_txtQuantity').fill(quantity.toString());
        }
        
        // Unchecking is Assembly?
        await this.page.waitForTimeout(1250);
        await this.page.getByRole('checkbox').first().click({ force: true });

        // Saving Detail
        await this.page.getByRole('button', { name: 'Save' }).click();

        await this.WaitToLoad();
        console.log(` Successfully replaced ${oldPartNumber} with ${newPartNumber} in ${ASM}`);
      }

      return true;

    } catch (error) {
      console.error(` Error replacing part in BOM:`, error);
      await this.takeScreenshot(`error_replace_bom_${ASMs}.png`);
      return false;
    }
  }

  /**
   * Navigate to an existing part's edit form.
   * Returns false if the part number cannot be found.
   */
  async navigateToEditPart(partNumber: string): Promise<boolean> {
    if (!this.page) throw new Error('Browser not started');

    console.log(` Navigating to part record: ${partNumber}`);
    await this.page.goto(this.config.url + '/IMS/PartMaint.aspx');
    await this.page.waitForLoadState('networkidle');

    // Filter the grid by part number
    await this.page.getByAltText('Filter Part Number column').fill(partNumber);
    await this.page.getByAltText('Filter Part Number column').press('Enter');
    await this.WaitToLoad();

    const selectBtn = this.page.getByTitle('Select').first();
    if (!await selectBtn.isVisible()) {
      console.log(` Part not found: ${partNumber}`);
      return false;
    }

    await selectBtn.click();
    await this.WaitToLoad();
    return true;
  }

  /**
   * Edit an existing part.  Only fields present in the update object are written;
   * everything else is left exactly as it is in TREQSO.
   */
  async editPart(update: PartUpdate): Promise<boolean> {
    if (!this.page) throw new Error('Browser not started');

    try {
      console.log(`Editing part: ${update.partNumber}`);

      const found = await this.navigateToEditPart(update.partNumber);
      if (!found) {
        console.error(` Part ${update.partNumber} not found in TREQSO`);
        return false;
      }

      // Update only the fields that were supplied
      if (update.partType !== undefined) {
        if(update.partType !== await this.page.locator('#ctl00_ContentPlaceHolder1_ddlPartType_Input').inputValue()){
          await this.page.getByRole('link', { name: 'Change Type' }).click();
          const frame = this.page.frameLocator('iframe[name="winChangeType"]');
          await frame.locator('#ctl00_ContentPlaceHolder1_ddlPartType_Input').fill(update.partType);
          await frame.locator('#ctl00_ContentPlaceHolder1_ddlPartType_Input').press('Enter');
          this.page.once('dialog', dialog => {
          dialog.accept();
          });
          await this.page.locator('iframe[name="winChangeType"]').contentFrame().getByRole('button', { name: 'Change Type' }).click();
          await this.WaitToLoad();
        }
      }

      if (update.partStatus !== undefined) {
        await this.page.locator('#ctl00_ContentPlaceHolder1_ddlPartStatus_Input').fill(update.partStatus);
      }
      
      if (update.partDescription !== undefined) {
        await this.page.locator('#ContentPlaceHolder1_txtPartDescription').fill(update.partDescription);
      }

      if (update.fullDescription !== undefined) {
        await this.page.locator('#ContentPlaceHolder1_txtPlainFullDescription').fill(update.fullDescription);
      }

      if (update.partCategory !== undefined) {
        await this.page.locator('#ctl00_ContentPlaceHolder1_ddlPartCategory_Input').fill(update.partCategory);
      }

      if (update.productCode !== undefined) {
        await this.page.locator('#ctl00_ContentPlaceHolder1_ddlProductCode_Input').fill(update.productCode);
      }

      if (update.salesGroup !== undefined) {
        await this.page.locator('#ctl00_ContentPlaceHolder1_ddlSalesGroup_Input').fill(update.salesGroup);
      }
      
      if (update.phaseNumber !== undefined) {
        await this.page.locator('#ctl00_ContentPlaceHolder1_ddlPhaseNumber_Input').fill(update.phaseNumber);
      }

      if (update.standardCost !== undefined) {
        await this.page.locator('#ctl00_ContentPlaceHolder1_numStandardCost').fill(update.standardCost);
      }

      if (update.unitOfMeasure !== undefined) {
        await this.page.locator('#ctl00_ContentPlaceHolder1_ddlUOM1_Input').fill(update.unitOfMeasure);
      }

      if (update.defaultCostField !== undefined) {
        await this.page.locator('#ctl00_ContentPlaceHolder1_ddlDefaultCostField_Input').fill(update.defaultCostField);
      }

      // Save the changes
      await this.page.getByRole('button', { name: 'Update', exact: true }).click();
      await this.WaitToLoad();

      console.log(` Part ${update.partNumber} updated successfully!`);
      return true;

    } catch (error) {
      console.error(`Error editing part ${update.partNumber}:`, error);
      await this.takeScreenshot(`error_edit_part_${update.partNumber}.png`);
      return false;
    }
  }

  /**
   * Edit multiple parts in batch from an array of partial updates.
   */
  async batchEditParts(updates: PartUpdate[]): Promise<Record<string, boolean>> {
    const results: Record<string, boolean> = {};

    for (const update of updates) {
      const success = await this.editPart(update);
      results[update.partNumber] = success;
      await this.page?.waitForTimeout(1250);
    }

    return results;
  }

  /**
   * Create multiple parts in batch
   */
  async batchCreateParts(parts: Part[]): Promise<Record<string, boolean>> {
    const results: Record<string, boolean> = {};

    for (const part of parts) {
      const success = await this.createPart(part);
      results[part.partNumber] = success;
      await this.page?.waitForTimeout(1250);
    }

    return results;
  }

  /**
   * Take a screenshot for debugging or documentation
   */
  async takeScreenshot(filename: string): Promise<void> {
    if (!this.page) throw new Error('Browser not started');
    await this.page.screenshot({ path: filename });
    console.log(`Screenshot saved: ${filename}`);
  }

  /**
   * Close the browser and clean up
   */
  async close(): Promise<void> {
    if (this.context) await this.context.close();
    if (this.browser) await this.browser.close();
    console.log('Browser closed.');
  }
}