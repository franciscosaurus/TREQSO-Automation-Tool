/**
 * TREQSO CLI - Command-line interface for TREQSO automation
 * Accepts JSON input from Python scripts for processing
 */

import { TREQSOAutomation, Part, PartUpdate, BOMLine, TREQSOConfig } from './treqso-automation';
import * as fs from 'fs';
import * as path from 'path';

interface CLICommand {
  action: 'create_parts' | 'edit_parts' | 'create_bom' | 'replace_part' | 'login_test' | 'print_MOs';
  config: TREQSOConfig;
  data?: any;
}

interface PrintData {
  reference_id: string;
}

interface CreatePartsData {
  parts: Part[];
}

interface EditPartsData {
  updates: PartUpdate[];
}

interface CreateBOMData {
  BOMs: [];
}

interface ReplacePartData {
  oldPartNumber: string;
  newPartNumber: string;
  updateQuantity?: string;
}

/**
 * Process command from JSON input
 */
async function processCommand(command: CLICommand): Promise<void> {
  const automation = new TREQSOAutomation(command.config);

  try {
    await automation.startBrowser();
    await automation.login();

    switch (command.action) {
      case 'print_MOs':
        await handlePrintMOs(automation, command.data as PrintData);
        break;
      case 'create_parts':
        await handleCreateParts(automation, command.data as CreatePartsData);
        break;

      case 'edit_parts':
        await handleEditParts(automation, command.data as EditPartsData);
        break;

      case 'create_bom':
        await handleCreateBOM(automation, command.data as CreateBOMData);
        break;

      case 'replace_part':
        await handleReplacePart(automation, command.data as ReplacePartData);
        break;

      case 'login_test':
        console.log('Login test successful!');
        await automation.takeScreenshot('login_success.png');
        writeResult({ success: true, message: 'Login successful' });
        break;

      default:
        throw new Error(`Unknown action: ${command.action}`);
    }

  } catch (error) {
    console.error('Error during automation:', error);
    writeResult({ 
      success: false, 
      error: error instanceof Error ? error.message : String(error) 
    });
    process.exit(1);
  } finally {
    await automation.close();
  }
}

/**
 * Handle creating multiple parts
 */
async function handlePrintMOs(
  automation: TREQSOAutomation, 
  data: PrintData
): Promise<void> {
  console.log(`Printing ${data.reference_id} Manufacturing Orders...`);
  const results = await automation.printMOs(data.reference_id);

  const successCount = Object.values(results).filter(Boolean).length;
  const totalCount = Object.keys(results).length;

  console.log(`\n=== Print MOs Summary ===`);
  console.log(`Successfully printed: ${successCount}/${totalCount} MOs`);

  const failures = Object.entries(results)
    .filter(([_, success]) => !success)
    .map(([referenceID, _]) => referenceID);

  if (failures.length > 0) {
    console.log('\nFailed parts:');
    failures.forEach(pn => console.log(`  - ${pn}`));
  }

  writeResult({
    success: successCount === totalCount,
    results,
    summary: {
      total: totalCount,
      successful: successCount,
      failed: failures.length,
      failures
    }
  });
}

/**
 * Handle creating multiple parts
 */
async function handleCreateParts(
  automation: TREQSOAutomation, 
  data: CreatePartsData
): Promise<void> {
  console.log(`Creating ${data.parts.length} parts...`);
  const results = await automation.batchCreateParts(data.parts);

  const successCount = Object.values(results).filter(Boolean).length;
  const totalCount = Object.keys(results).length;

  console.log(`\n=== Batch Part Creation Summary ===`);
  console.log(`Successfully created: ${successCount}/${totalCount} parts`);

  const failures = Object.entries(results)
    .filter(([_, success]) => !success)
    .map(([partNumber, _]) => partNumber);

  if (failures.length > 0) {
    console.log('\nFailed parts:');
    failures.forEach(pn => console.log(`  - ${pn}`));
  }

  writeResult({
    success: successCount === totalCount,
    results,
    summary: {
      total: totalCount,
      successful: successCount,
      failed: failures.length,
      failures
    }
  });
}

/**
 * Handle editing multiple existing parts
 */
async function handleEditParts(
  automation: TREQSOAutomation,
  data: EditPartsData
): Promise<void> {
  console.log(`Editing ${data.updates.length} parts...`);
  const results = await automation.batchEditParts(data.updates);

  const successCount = Object.values(results).filter(Boolean).length;
  const totalCount = Object.keys(results).length;

  console.log(`\n=== Batch Part Edit Summary ===`);
  console.log(`Successfully updated: ${successCount}/${totalCount} parts`);

  const failures = Object.entries(results)
    .filter(([_, success]) => !success)
    .map(([partNumber, _]) => partNumber);

  if (failures.length > 0) {
    console.log('\nFailed parts:');
    failures.forEach(pn => console.log(`  - ${pn}`));
  }

  writeResult({
    success: successCount === totalCount,
    results,
    summary: {
      total: totalCount,
      successful: successCount,
      failed: failures.length,
      failures
    }
  });
}

/**
 * Handle creating a BOM
 */
async function handleCreateBOM(
  automation: TREQSOAutomation,
  data: CreateBOMData
): Promise<void> {
  const success = await automation.createBOM(data.BOMs);

  if (!success) {
    console.log(`✗ Failed to create BOM for ${data.BOMs}`);
  }

  writeResult({
    success,
    BOM_Data: data,
  });
}

/**
 * Handle replacing a part in a BOM
 */
async function handleReplacePart(
  automation: TREQSOAutomation,
  data: ReplacePartData
): Promise<void> {
  console.log(`Replacing ${data.oldPartNumber} with ${data.newPartNumber}...`);
  const success = await automation.massReplaceBOMParts(
    data.oldPartNumber,
    data.newPartNumber,
    data.updateQuantity
  );

  if (success) {
    console.log(`✓ Successfully replaced part`);
  } else {
    console.log(`✗ Failed to replace part`);
  }

  writeResult({
    success,
    ...data
  });
}

/**
 * Write result to a JSON file for Python to read
 */
function writeResult(result: any): void {
  const resultPath = path.join(process.cwd(), 'result.json');
  fs.writeFileSync(resultPath, JSON.stringify(result, null, 2));
  console.log(`\nResult written to: ${resultPath}`);
}

/**
 * Main entry point
 */
async function main(): Promise<void> {
  // Check for input file argument
  if (process.argv.length < 3) {
    console.error('Usage: node cli.js <input.json>');
    console.error('\nExample input.json:');
    console.error(JSON.stringify({
      action: 'create_parts',
      config: {
        url: 'https://your-treqso.com',
        username: 'user',
        password: 'pass',
        headless: false
      },
      data: {
        parts: [
          {
            partNumber: 'TEST-001',
            description: 'Test Part',
            revision: 'A'
          }
        ]
      }
    }, null, 2));
    process.exit(1);
  }

  const inputFile = process.argv[2];

  // Read and parse input JSON
  if (!fs.existsSync(inputFile)) {
    console.error(`Error: Input file '${inputFile}' not found`);
    process.exit(1);
  }

  const inputData = fs.readFileSync(inputFile, 'utf-8');
  const command: CLICommand = JSON.parse(inputData);

  // Process the command
  await processCommand(command);
}

// Run the CLI
main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
