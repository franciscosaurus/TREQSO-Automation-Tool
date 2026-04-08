"""
Python Data Processor for TREQSO Automation
Handles CSV processing and interfaces with TypeScript Playwright automation
"""

import csv
import json
import subprocess
import os
import sys
from typing import List, Dict, Any
from dataclasses import dataclass
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()


@dataclass
class Part:
    """Represents a part in TREQSO"""
    partNumber: str
    partDescription: str
    fullDescription: str
    partCategory: str
    productCode: str
    salesGroup: str
    partType: str
    phaseNumber: str
    standardCost: str
    unitOfMeasure: str
    defaultCostField: str
    

    def to_dict(self):
        """Convert to dictionary, excluding None values"""
        result = {
            'partNumber': self.partNumber,
            'partDescription': self.partDescription,
            'fullDescription': self.fullDescription,
            'partCategory': self.partCategory,
            'productCode': self.productCode,
            'salesGroup': self.salesGroup,
            'partType': self.partType,
            'phaseNumber': self.phaseNumber,
            'standardCost': self.standardCost,
            'unitOfMeasure': self.unitOfMeasure,
            'defaultCostField': self.defaultCostField
        }
        return result


@dataclass
class BOMLine:
    """Represents a line item in a BOM"""
    BOMSequence: str
    BOMOption: str
    partNumber: str
    quantity: float
    doRollup: bool

    def to_dict(self):
        """Convert to dictionary, excluding None values"""
        result = {
            'BOMSequence': self.BOMSequence,
            'BOMOption': self.BOMOption,
            'partNumber': self.partNumber,
            'quantity': self.quantity,
            'doRollup': self.doRollup
        }
        return result


class TREQSODataProcessor:
    """Processes data and interfaces with TypeScript automation"""
    
    def __init__(self):
        self.log_callback = None
        self.config = {
            'url': os.getenv('TREQSO_URL', 'https://your-treqso.com'),
            'company': os.getenv('COMPANY', 'CargoTest'),
            'headless': os.getenv('TREQSO_HEADLESS', 'false').lower() == 'true',
            'slowMo': int(os.getenv('TREQSO_SLOW_MO', '0'))
        }

    def _get_app_dir(self) -> str:
        """
        Return the application's root directory.

        When running as a PyInstaller single-file exe the real executable sits at
        {install_dir}/TREQSO_Automation.exe, so dirname(sys.executable) is the
        install root where node_modules/, dist/, node_portable/ etc. all live.

        When running from Python source the script lives in the project root,
        so we use its directory directly.
        """
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))

    def _get_node_path(self) -> str:
        """
        Resolve the node executable to use.

        Priority:
          1. node_portable/node.exe next to the application (bundled / installed)
          2. 'node' on the system PATH (developer machines)
        """
        bundled = os.path.join(self._get_app_dir(), 'node_portable', 'node.exe')
        if os.path.exists(bundled):
            return bundled
        return 'node'

    def load_parts_from_csv(self, filename: str) -> List[Part]:
        """
        Load parts from a CSV file.
        
        CSV Format:
        partNumber,partDescription,fullDescription,partCategory,productCode,salesGroup,partType,phaseNumber,orderType,standardCost,unitOfMeasure,defaultCostField
        Ex. Part Number,Ex. Part Description,Ex. Full Description,4041 (PART),40 (MANUFACTURED),Ex. Sales Group,B (Buy),Ex. Phase Number,Ex. Order Type, Ex. Standard Cost,EA (Each),Ex. Cost Field
        
        Args:
            filename: Path to CSV file
            
        Returns:
            List of Part objects
        """
        parts = []
        
        with open(filename, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                part = Part(
                    partNumber=row['partNumber'],
                    partDescription=row['partDescription'],
                    fullDescription=row['fullDescription'],
                    partCategory=row['partCategory'],
                    productCode=row['productCode'],
                    salesGroup=row['salesGroup'],
                    partType=row['partType'],
                    phaseNumber=row['phaseNumber'],
                    standardCost=row['standardCost'],
                    unitOfMeasure=row['unitOfMeasure'],
                    defaultCostField=row['defaultCostField']
                )
                parts.append(part)
                
        print(f"✓ Loaded {len(parts)} parts from {filename}")
        return parts

    def load_bom_from_csv(self, filename: str) -> Dict[str, List[BOMLine]]:
        """
        Load BOM from a CSV file.
        
        CSV Format:
        assembly_part_number,BOMSequence,BOMOption,partNumber,quantity,doRollup
        EX-ASMS2-0,1,0,EX-PRTS2-2,1,TRUE
        EX-ASMS2-1,1,0,EX-PRTS2-7,5,TRUE
        
        Args:
            filename: Path to CSV file
            
        Returns:
            Tuple of (assembly_part_number, list of BOMLine objects)
        """
        boms = {}
        bom_lines = []
        assembly_part_number = None
        
        with open(filename, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                
                bom_line = BOMLine(
                    BOMSequence=(row['BOMSequence']),
                    BOMOption=row['BOMOption'],
                    partNumber=row['partNumber'],
                    quantity=float(row['quantity']),
                    doRollup=bool(row['doRollup'])
                )
                                   
                if assembly_part_number == None:
                    assembly_part_number = row['assembly_part_number']
                elif assembly_part_number != row['assembly_part_number']:
                    boms[assembly_part_number] = bom_lines
                    assembly_part_number = row['assembly_part_number']
                    bom_lines = []
                bom_lines.append(bom_line)

            boms[assembly_part_number] =  bom_lines
        
        print(f"✓ Loaded {len(boms)} BOMs from {filename}")
        return boms

    # def execute_automation(self, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
    def execute_automation(self, action: str, data: Dict[str, Any], log_callback=None) -> Dict[str, Any]:    
        """
        Execute TypeScript automation via CLI.

        Uses the bundled node.exe when available, otherwise falls back to the
        system node.  All file paths are resolved relative to the application
        root so the subprocess works correctly whether running from source,
        from the raw PyInstaller exe, or from the installed location.

        Args:
            action: Action to perform (create_parts, create_bom, replace_part, ...)
            data:   Data payload for the action

        Returns:
            Result dictionary from TypeScript automation
        """
        if log_callback is None:
            log_callback = getattr(self, 'log_callback', None)

        start_time = time.time()

        app_dir    = self._get_app_dir()
        node_exe   = self._get_node_path()
        cli_path   = os.path.join(app_dir, 'dist', 'cli.js')
        input_file = os.path.join(app_dir, 'automation_input.json')
        result_file = os.path.join(app_dir, 'result.json')

        # Build command JSON
        command = {
            'action': action,
            'config': self.config,
            'data':   data
        }

        with open(input_file, 'w') as f:
            json.dump(command, f, indent=2)

        print(f"\n→ Executing {action} automation...")
        print(f"  node   : {node_exe}")
        print(f"  cli    : {cli_path}")

        # Build environment: ensure the bundled node directory is on PATH so
        # any child scripts (e.g. playwright.cmd) can find node.exe too.
        env = os.environ.copy()
        if os.path.isabs(node_exe):
            node_dir = os.path.dirname(node_exe)
            env['PATH'] = node_dir + os.pathsep + env.get('PATH', '')

        try:
            # Run the TypeScript CLI
            process = subprocess.Popen(
                [node_exe, cli_path, input_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=app_dir,
                env=env
            )

            # Stream stdout line by line in real time
            for line in process.stdout:
                line = line.rstrip('\n')
                if line:
                    print(line)
                    if log_callback:
                        log_callback(line)

            process.wait(timeout=3600)

            # Drain stderr after process finishes
            stderr_output = process.stderr.read()
            if stderr_output:
                for line in stderr_output.splitlines():
                    if line.strip():
                        print(f"[stderr] {line}")
                        if log_callback:
                            log_callback(f"[stderr] {line}")

            if os.path.exists(result_file):
                with open(result_file, 'r') as f:
                    result_data = json.load(f)

                elapsed = time.time() - start_time
                minutes = int(elapsed // 60)
                seconds = elapsed % 60
                time_str = f"{minutes}m {seconds:.1f}s" if minutes else f"{seconds:.2f}s"

                print(f"✓ {action} completed in {time_str}")
                if log_callback:
                    log_callback(f"✓ {action} completed in {time_str}")
                return result_data
            else:
                return {
                    'success': False,
                    'error':   'No result file generated — check that node.exe and dist/cli.js are present'
                }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error':   'Automation timed out after 60 minutes'
            }
        except FileNotFoundError:
            return {
                'success': False,
                'error':   (
                    f"Could not launch node executable: '{node_exe}'. "
                    "Ensure node_portable/node.exe is present in the install directory, "
                    "or that Node.js is installed and available on the system PATH."
                )
            }
        except Exception as e:
            return {
                'success': False,
                'error':   str(e)
            }
        finally:
            if os.path.exists(input_file):
                os.remove(input_file)

    def create_parts_from_csv(self, csv_file: str) -> Dict[str, Any]:
        """
        Create parts from CSV file
        
        Args:
            csv_file: Path to parts CSV file
            
        Returns:
            Result dictionary
        """
        parts = self.load_parts_from_csv(csv_file)
        
        data = {
            'parts': [part.to_dict() for part in parts]
        }
        
        return self.execute_automation('create_parts', data)

    def load_part_updates_from_csv(self, filename: str) -> List[Dict[str, str]]:
        """
        Load part update records from a CSV file.

        Only the columns actually present in the CSV file are read — columns
        you omit are simply not sent to TREQSO, leaving those fields unchanged.
        Within a row, blank cells are also skipped (the field is left as-is).

        Required column:
            partNumber  — used to locate the part record in TREQSO

        Optional columns (include only the ones you want to change):
            partDescription, fullDescription, partCategory, productCode,
            salesGroup, partType, phaseNumber, orderType, standardCost,
            unitOfMeasure, defaultCostField

        Args:
            filename: Path to CSV file

        Returns:
            List of update dicts, each containing only the fields to change
        """
        # All fields that can be updated (partNumber is always required)
        editable_fields = {
            'partStatus', 'partDescription', 'fullDescription', 'partCategory',
            'productCode', 'salesGroup', 'partType', 'phaseNumber',
            'standardCost', 'unitOfMeasure', 'defaultCostField'
        }

        updates = []
        with open(filename, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            if 'partNumber' not in (reader.fieldnames or []):
                raise ValueError("CSV must contain a 'partNumber' column.")

            # Which optional fields are actually in this file
            present_fields = editable_fields & set(reader.fieldnames or [])

            for row in reader:
                pn = row.get('partNumber', '').strip()
                if not pn:
                    continue  # skip blank rows

                update: Dict[str, str] = {'partNumber': pn}

                # Only include a field if the cell has a non-blank value
                for field in present_fields:
                    value = row.get(field, '').strip()
                    if value:
                        update[field] = value

                updates.append(update)

        print(f"✓ Loaded {len(updates)} part updates from {filename}")
        fields_in_use = sorted(present_fields & {k for u in updates for k in u})
        print(f"  Fields being updated: {', '.join(fields_in_use) if fields_in_use else 'none'}")
        return updates

    def edit_parts_from_csv(self, csv_file: str) -> Dict[str, Any]:
        """
        Edit existing parts in TREQSO from a CSV file.

        Args:
            csv_file: Path to CSV containing partNumber + any editable field columns

        Returns:
            Result dictionary
        """
        updates = self.load_part_updates_from_csv(csv_file)
        data = {'updates': updates}
        return self.execute_automation('edit_parts', data)

    def create_bom_from_csv(self, csv_file: str) -> Dict[str, Any]:
        """
        Create BOM from CSV file
        
        Args:
            csv_file: Path to BOM CSV file
            
        Returns:
            Result dictionary
        """
        BOMs = self.load_bom_from_csv(csv_file)
        returnValue = {'': any}
        data = {}
        numberBOM = 0

        for asm in BOMs:
            tempData = {
            'assemblyPartNumber': asm,
            'bomLines': [bomLine.to_dict() for bomLine in BOMs[asm]]
            }
            data[numberBOM] = tempData
            numberBOM = numberBOM + 1

        returnValue = self.execute_automation('create_bom', {'create_bom': numberBOM, 'BOMs': data})
     
        return returnValue

    def replace_part(
        self, 
        old_part_number: str,
        new_part_number: str,
        update_quantity: str | None = None
    ) -> Dict[str, Any]:
        """
        Replace a part in a BOM
        
        Args:
            assembly_part_number: Assembly containing the BOM
            old_part_number: Part to replace
            new_part_number: Replacement part
            update_quantity: Optional new quantity
            
        Returns:
            Result dictionary
        """
        data = {
            'oldPartNumber': old_part_number,
            'newPartNumber': new_part_number
        }
        
        if update_quantity is not None:
            data['updateQuantity'] = update_quantity
        
        return self.execute_automation('replace_part', data)

    def test_login(self) -> Dict[str, Any]:
        """Test TREQSO login"""
        return self.execute_automation('login_test', {})
    
    def print_MOs(
        self,
        reference_id: str,
    ) -> Dict[str, Any]:
        """Print the child MOs of a parent MO"""

        data = {
            'reference_id': reference_id,
        }

        return self.execute_automation('print_MOs', data)


def main():
    """Main CLI interface"""
    import sys
    
    if len(sys.argv) < 2:
        print("TREQSO Data Processor - CSV to TREQSO Automation")
        print("\nUsage:")
        print("  python treqso_processor.py parts <csv_file>")
        print("  python treqso_processor.py bom <csv_file>")
        print("  python treqso_processor.py replace <assembly_pn> <old_pn> <new_pn> [quantity]")
        print("  python treqso_processor.py test")
        print("\nExamples:")
        print("  python treqso_processor.py parts sample_parts.csv")
        print("  python treqso_processor.py bom sample_bom.csv")
        print("  python treqso_processor.py replace PCB-001-MAIN RES-001 RES-002 4")
        print("  python treqso_processor.py test  # Test login only")
        sys.exit(1)
    
    processor = TREQSODataProcessor()
    command = sys.argv[1]
    
    try:
        if command == 'print':
            if len(sys.argv) < 3:
                print("Error: CSV file required")
                sys.exit(1)
            result = processor.print_MOs(sys.argv[2])

        if command == 'parts':
            if len(sys.argv) < 3:
                print("Error: CSV file required")
                sys.exit(1)
            result = processor.create_parts_from_csv(sys.argv[2])
            
        elif command == 'bom':
            if len(sys.argv) < 3:
                print("Error: CSV file required")
                sys.exit(1)
            result = processor.create_bom_from_csv(sys.argv[2])
            
        elif command == 'replace':
            if len(sys.argv) < 4:
                print("Error: Arguments required: <old_pn> <new_pn> [quantity]")
                sys.exit(1)
            
            old_pn = sys.argv[2]
            new_pn = sys.argv[3]
            quantity = str(sys.argv[4]) if len(sys.argv) > 4 else None
            
            result = processor.replace_part(old_pn, new_pn, quantity)
            
        elif command == 'test':
            print("Testing TREQSO login...")
            result = processor.test_login()
            
        else:
            print(f"Error: Unknown command '{command}'")
            sys.exit(1)
        
        # Print result summary
        print("\n" + "="*50)
        print("RESULT SUMMARY")
        print("="*50)
        print(json.dumps(result, indent=2))
        
        if result.get('success'):
            print("\n✓ Operation completed successfully!")
            sys.exit(0)
        else:
            print("\n✗ Operation failed!")
            sys.exit(1)
            
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
