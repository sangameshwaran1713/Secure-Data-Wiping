#!/usr/bin/env python3
"""
Sample IT Assets Generator

Creates realistic sample IT assets for demonstration and testing purposes.
This module generates various device types with realistic specifications
for comprehensive system demonstration.
"""

import sys
import os
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dataclasses import asdict

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

from secure_data_wiping.utils.data_models import DeviceInfo, DeviceType


class SampleITAssetsGenerator:
    """Generates sample IT assets for demonstration purposes."""
    
    def __init__(self, output_dir: str = None):
        """
        Initialize the sample assets generator.
        
        Args:
            output_dir: Directory to store sample asset files
        """
        self.output_dir = Path(output_dir) if output_dir else Path('demo/sample_assets')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Realistic device specifications
        self.device_specs = {
            DeviceType.HDD: [
                {"manufacturer": "Seagate", "model": "Barracuda_2TB", "capacity": 2000000000000, "connection": "SATA"},
                {"manufacturer": "Western_Digital", "model": "Blue_1TB", "capacity": 1000000000000, "connection": "SATA"},
                {"manufacturer": "Toshiba", "model": "P300_3TB", "capacity": 3000000000000, "connection": "SATA"},
                {"manufacturer": "HGST", "model": "Ultrastar_4TB", "capacity": 4000000000000, "connection": "SATA"},
                {"manufacturer": "Seagate", "model": "IronWolf_8TB", "capacity": 8000000000000, "connection": "SATA"},
            ],
            DeviceType.SSD: [
                {"manufacturer": "Samsung", "model": "EVO_860_500GB", "capacity": 500000000000, "connection": "SATA"},
                {"manufacturer": "Crucial", "model": "MX500_1TB", "capacity": 1000000000000, "connection": "SATA"},
                {"manufacturer": "Kingston", "model": "A2000_250GB", "capacity": 250000000000, "connection": "NVMe"},
                {"manufacturer": "Intel", "model": "660p_512GB", "capacity": 512000000000, "connection": "NVMe"},
                {"manufacturer": "WD", "model": "Black_SN750_1TB", "capacity": 1000000000000, "connection": "NVMe"},
            ],
            DeviceType.USB: [
                {"manufacturer": "SanDisk", "model": "Ultra_32GB", "capacity": 32000000000, "connection": "USB_3.0"},
                {"manufacturer": "Kingston", "model": "DataTraveler_64GB", "capacity": 64000000000, "connection": "USB_3.0"},
                {"manufacturer": "Corsair", "model": "Flash_Voyager_128GB", "capacity": 128000000000, "connection": "USB_3.1"},
                {"manufacturer": "Lexar", "model": "JumpDrive_16GB", "capacity": 16000000000, "connection": "USB_2.0"},
                {"manufacturer": "PNY", "model": "Turbo_256GB", "capacity": 256000000000, "connection": "USB_3.2"},
            ],
            DeviceType.NVME: [
                {"manufacturer": "Samsung", "model": "980_PRO_1TB", "capacity": 1000000000000, "connection": "PCIe_4.0"},
                {"manufacturer": "WD", "model": "Black_SN850_2TB", "capacity": 2000000000000, "connection": "PCIe_4.0"},
                {"manufacturer": "Crucial", "model": "P5_500GB", "capacity": 500000000000, "connection": "PCIe_3.0"},
                {"manufacturer": "Intel", "model": "Optane_905P_480GB", "capacity": 480000000000, "connection": "PCIe_3.0"},
                {"manufacturer": "Corsair", "model": "MP600_1TB", "capacity": 1000000000000, "connection": "PCIe_4.0"},
            ],
            DeviceType.SD_CARD: [
                {"manufacturer": "SanDisk", "model": "Extreme_64GB", "capacity": 64000000000, "connection": "SD"},
                {"manufacturer": "Samsung", "model": "EVO_Select_128GB", "capacity": 128000000000, "connection": "SD"},
                {"manufacturer": "Lexar", "model": "Professional_32GB", "capacity": 32000000000, "connection": "SD"},
                {"manufacturer": "Kingston", "model": "Canvas_React_256GB", "capacity": 256000000000, "connection": "SD"},
                {"manufacturer": "PNY", "model": "Elite_X_16GB", "capacity": 16000000000, "connection": "SD"},
            ],
            DeviceType.OTHER: [
                {"manufacturer": "Generic", "model": "Storage_Device_1TB", "capacity": 1000000000000, "connection": "Unknown"},
                {"manufacturer": "Generic", "model": "Storage_Device_500GB", "capacity": 500000000000, "connection": "Unknown"},
                {"manufacturer": "Generic", "model": "Storage_Device_2TB", "capacity": 2000000000000, "connection": "Unknown"},
                {"manufacturer": "Generic", "model": "Storage_Device_250GB", "capacity": 250000000000, "connection": "Unknown"},
                {"manufacturer": "Generic", "model": "Storage_Device_4TB", "capacity": 4000000000000, "connection": "Unknown"},
            ]
        }
    
    def generate_device_id(self, device_type: DeviceType, index: int) -> str:
        """
        Generate a realistic device ID.
        
        Args:
            device_type: Type of device
            index: Device index for uniqueness
            
        Returns:
            Generated device ID
        """
        type_prefix = {
            DeviceType.HDD: "HDD",
            DeviceType.SSD: "SSD", 
            DeviceType.USB: "USB",
            DeviceType.NVME: "NVM",
            DeviceType.SD_CARD: "SDC",
            DeviceType.OTHER: "OTH"
        }
        
        return f"{type_prefix[device_type]}{index:03d}_{datetime.now().strftime('%Y%m%d')}"
    
    def generate_serial_number(self, manufacturer: str, index: int) -> str:
        """
        Generate a realistic serial number.
        
        Args:
            manufacturer: Device manufacturer
            index: Device index
            
        Returns:
            Generated serial number
        """
        mfg_codes = {
            "Samsung": "SAM",
            "Western_Digital": "WDC", 
            "Seagate": "STG",
            "Crucial": "CRU",
            "Kingston": "KNG",
            "Intel": "INT",
            "SanDisk": "SDK",
            "Corsair": "COR",
            "Toshiba": "TSB",
            "HGST": "HGS",
            "Lexar": "LEX",
            "PNY": "PNY",
            "Generic": "GEN"
        }
        
        code = mfg_codes.get(manufacturer, "UNK")
        return f"{code}{index:06d}{datetime.now().strftime('%y%m')}"
    
    def create_sample_device(self, device_type: DeviceType, index: int) -> DeviceInfo:
        """
        Create a sample device with realistic specifications.
        
        Args:
            device_type: Type of device to create
            index: Device index for uniqueness
            
        Returns:
            DeviceInfo object with sample data
        """
        specs = self.device_specs[device_type]
        spec = specs[index % len(specs)]
        
        device_id = self.generate_device_id(device_type, index)
        serial_number = self.generate_serial_number(spec["manufacturer"], index)
        
        return DeviceInfo(
            device_id=device_id,
            device_type=device_type,
            capacity=spec["capacity"],
            manufacturer=spec["manufacturer"],
            model=spec["model"],
            serial_number=serial_number,
            connection_type=spec["connection"]
        )
    
    def create_sample_asset_batch(self, count_per_type: int = 5) -> List[DeviceInfo]:
        """
        Create a batch of sample IT assets.
        
        Args:
            count_per_type: Number of devices per device type
            
        Returns:
            List of sample DeviceInfo objects
        """
        devices = []
        
        for device_type in DeviceType:
            for i in range(count_per_type):
                device = self.create_sample_device(device_type, i + 1)
                devices.append(device)
        
        return devices
    
    def create_sample_data_files(self, devices: List[DeviceInfo]) -> Dict[str, str]:
        """
        Create sample data files for each device.
        
        Args:
            devices: List of devices to create files for
            
        Returns:
            Dictionary mapping device_id to file path
        """
        file_paths = {}
        
        for device in devices:
            # Create sample data file
            file_path = self.output_dir / f"{device.device_id}_sample_data.tmp"
            
            # Generate realistic sample data based on device type
            if device.device_type == DeviceType.HDD:
                sample_data = self._generate_hdd_sample_data(device)
            elif device.device_type == DeviceType.SSD:
                sample_data = self._generate_ssd_sample_data(device)
            elif device.device_type == DeviceType.USB:
                sample_data = self._generate_usb_sample_data(device)
            elif device.device_type == DeviceType.NVME:
                sample_data = self._generate_nvme_sample_data(device)
            elif device.device_type == DeviceType.SD_CARD:
                sample_data = self._generate_sd_card_sample_data(device)
            else:  # OTHER
                sample_data = self._generate_other_sample_data(device)
            
            # Write sample data to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(sample_data)
            
            file_paths[device.device_id] = str(file_path)
        
        return file_paths
    
    def _generate_hdd_sample_data(self, device: DeviceInfo) -> str:
        """Generate sample data for HDD devices."""
        return f"""# Sample Data for HDD Device: {device.device_id}
# Manufacturer: {device.manufacturer}
# Model: {device.model}
# Capacity: {device.capacity:,} bytes
# Serial: {device.serial_number}

# Simulated file system data
/boot/vmlinuz-5.4.0-generic
/etc/passwd
/home/user/documents/financial_report_2023.xlsx
/home/user/documents/personal_photos/
/var/log/system.log
/tmp/cache_files/
/usr/bin/applications/

# Simulated database records
user_id,username,email,created_date
1001,john_doe,john@company.com,2023-01-15
1002,jane_smith,jane@company.com,2023-02-20
1003,bob_wilson,bob@company.com,2023-03-10

# Simulated configuration files
server_config={{
    "database_host": "192.168.1.100",
    "api_key": "sk_test_12345abcdef",
    "encryption_key": "aes256_key_sample"
}}

# Large data block simulation
{"DATA_BLOCK_" * 1000}

# End of sample data for {device.device_id}
"""
    
    def _generate_ssd_sample_data(self, device: DeviceInfo) -> str:
        """Generate sample data for SSD devices."""
        return f"""# Sample Data for SSD Device: {device.device_id}
# Manufacturer: {device.manufacturer}
# Model: {device.model}
# Capacity: {device.capacity:,} bytes
# Serial: {device.serial_number}

# Simulated application data
/Applications/PhotoEditor.app
/Applications/VideoProcessor.app
/Users/designer/Projects/client_logos/
/Users/designer/Projects/marketing_materials/
/System/Library/Frameworks/

# Simulated user data
project_name,client,status,deadline
Website_Redesign,TechCorp,In_Progress,2024-03-15
Mobile_App_UI,StartupXYZ,Completed,2024-01-30
Brand_Identity,LocalBiz,Planning,2024-04-01

# Simulated cache and temporary files
cache_entry_001: user_session_data_encrypted
cache_entry_002: api_response_cached_data
temp_file_001: image_processing_buffer
temp_file_002: video_render_queue

# Performance-optimized data blocks
{"FAST_ACCESS_DATA_" * 800}

# End of sample data for {device.device_id}
"""
    
    def _generate_usb_sample_data(self, device: DeviceInfo) -> str:
        """Generate sample data for USB devices."""
        return f"""# Sample Data for USB Device: {device.device_id}
# Manufacturer: {device.manufacturer}
# Model: {device.model}
# Capacity: {device.capacity:,} bytes
# Serial: {device.serial_number}

# Simulated portable files
Documents/
  - presentation_slides.pptx
  - meeting_notes.docx
  - budget_spreadsheet.xlsx
  - project_timeline.pdf

Photos/
  - vacation_2023/
  - family_events/
  - work_conference/

Software/
  - portable_apps/
  - drivers/
  - utilities/

# Simulated personal data
contact_name,phone,email,notes
Alice_Johnson,555-0101,alice@email.com,Project_Manager
Bob_Smith,555-0102,bob@email.com,Technical_Lead
Carol_Davis,555-0103,carol@email.com,Designer

# Simulated backup data
backup_timestamp: {datetime.now().isoformat()}
backup_source: /Users/username/Documents
backup_size: {device.capacity // 2} bytes

# Portable data blocks
{"PORTABLE_DATA_" * 200}

# End of sample data for {device.device_id}
"""
    
    def _generate_nvme_sample_data(self, device: DeviceInfo) -> str:
        """Generate sample data for NVMe devices."""
        return f"""# Sample Data for NVMe Device: {device.device_id}
# Manufacturer: {device.manufacturer}
# Model: {device.model}
# Capacity: {device.capacity:,} bytes
# Serial: {device.serial_number}

# Simulated high-performance application data
/Games/AAA_Game_Title/assets/textures/
/Games/AAA_Game_Title/assets/models/
/Games/AAA_Game_Title/saves/
/Development/IDEs/
/Development/Compilers/
/Development/VirtualMachines/

# Simulated development data
repository,language,size_mb,last_commit
web_application,JavaScript,245,2024-01-08T10:30:00Z
mobile_app,Swift,189,2024-01-07T15:45:00Z
data_pipeline,Python,156,2024-01-08T09:15:00Z
game_engine,C++,892,2024-01-06T14:20:00Z

# Simulated high-speed cache
nvme_cache_block_001: ultra_fast_access_data
nvme_cache_block_002: real_time_processing_buffer
nvme_cache_block_003: ai_model_inference_cache

# High-performance data blocks
{"HIGH_SPEED_DATA_" * 1200}

# End of sample data for {device.device_id}
"""
    
    def save_device_inventory(self, devices: List[DeviceInfo]) -> str:
        """
        Save device inventory to JSON file.
        
        Args:
            devices: List of devices to save
            
        Returns:
            Path to saved inventory file
        """
        inventory_path = self.output_dir / "device_inventory.json"
        
        inventory_data = {
            "generated_at": datetime.now().isoformat(),
            "total_devices": len(devices),
            "device_types": {
                device_type.value: len([d for d in devices if d.device_type == device_type])
                for device_type in DeviceType
            },
            "devices": [asdict(device) for device in devices]
        }
        
        with open(inventory_path, 'w', encoding='utf-8') as f:
            json.dump(inventory_data, f, indent=2, default=str)
        
        return str(inventory_path)
    
    def create_demo_scenarios(self) -> Dict[str, List[DeviceInfo]]:
        """
        Create different demonstration scenarios.
        
        Returns:
            Dictionary of scenario names to device lists
        """
        scenarios = {}
        
        # Scenario 1: Small Office Setup
        scenarios["small_office"] = [
            self.create_sample_device(DeviceType.HDD, 1),
            self.create_sample_device(DeviceType.SSD, 1),
            self.create_sample_device(DeviceType.USB, 1),
        ]
        
        # Scenario 2: Data Center Decommission
        scenarios["data_center"] = [
            self.create_sample_device(DeviceType.HDD, i) for i in range(1, 6)
        ] + [
            self.create_sample_device(DeviceType.SSD, i) for i in range(1, 4)
        ] + [
            self.create_sample_device(DeviceType.NVME, i) for i in range(1, 3)
        ]
        
        # Scenario 3: Development Workstation
        scenarios["dev_workstation"] = [
            self.create_sample_device(DeviceType.NVME, 1),
            self.create_sample_device(DeviceType.SSD, 1),
            self.create_sample_device(DeviceType.HDD, 1),
            self.create_sample_device(DeviceType.USB, 1),
            self.create_sample_device(DeviceType.USB, 2),
        ]
        
        # Scenario 4: Enterprise Batch Processing
        scenarios["enterprise_batch"] = self.create_sample_asset_batch(count_per_type=8)
        
        return scenarios
    
    def generate_complete_demo_environment(self) -> Dict[str, Any]:
        """
        Generate a complete demonstration environment.
        
        Returns:
            Dictionary containing all demo environment data
        """
        print("🔧 Generating Sample IT Assets for Demonstration...")
        
        # Create scenarios
        scenarios = self.create_demo_scenarios()
        
        # Create data files for each scenario
        scenario_files = {}
        for scenario_name, devices in scenarios.items():
            print(f"  Creating {scenario_name} scenario ({len(devices)} devices)...")
            files = self.create_sample_data_files(devices)
            scenario_files[scenario_name] = files
            
            # Save scenario inventory
            scenario_inventory_path = self.output_dir / f"{scenario_name}_inventory.json"
            with open(scenario_inventory_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "scenario": scenario_name,
                    "devices": [asdict(device) for device in devices],
                    "data_files": files
                }, f, indent=2, default=str)
        
        # Create master inventory
        all_devices = []
        for devices in scenarios.values():
            all_devices.extend(devices)
        
        inventory_path = self.save_device_inventory(all_devices)
        
        demo_environment = {
            "generated_at": datetime.now().isoformat(),
            "total_devices": len(all_devices),
            "scenarios": scenarios,
            "scenario_files": scenario_files,
            "inventory_path": inventory_path,
            "output_directory": str(self.output_dir)
        }
        
        print(f"✅ Generated {len(all_devices)} sample IT assets across {len(scenarios)} scenarios")
        print(f"📁 Assets saved to: {self.output_dir}")
        
        return demo_environment


    def _generate_sd_card_sample_data(self, device: DeviceInfo) -> str:
        """Generate sample data for SD card devices."""
        return f"""# Sample Data for SD Card Device: {device.device_id}
# Manufacturer: {device.manufacturer}
# Model: {device.model}
# Capacity: {device.capacity:,} bytes
# Serial: {device.serial_number}

# Simulated camera and mobile data
DCIM/
  - Camera/
    - IMG_001.jpg
    - IMG_002.jpg
    - VID_001.mp4
  - Screenshots/
    - Screenshot_001.png
    - Screenshot_002.png

Music/
  - Playlist_001/
  - Favorites/
  - Downloaded/

Documents/
  - Notes.txt
  - Contacts_backup.vcf
  - Calendar_export.ics

# Simulated mobile app data
app_data={{
    "contacts": 150,
    "messages": 2500,
    "photos": 450,
    "videos": 25,
    "apps_installed": 85
}}

# Mobile device backup data
backup_info={{
    "device_model": "Mobile_Device",
    "os_version": "Android_12",
    "backup_date": "{datetime.now().isoformat()}",
    "data_size": {device.capacity // 3}
}}

# Portable media blocks
{"MOBILE_DATA_" * 150}

# End of sample data for {device.device_id}
"""
    
    def _generate_other_sample_data(self, device: DeviceInfo) -> str:
        """Generate sample data for other/unknown device types."""
        return f"""# Sample Data for Other Device: {device.device_id}
# Manufacturer: {device.manufacturer}
# Model: {device.model}
# Capacity: {device.capacity:,} bytes
# Serial: {device.serial_number}

# Generic storage device data
Storage/
  - Data/
    - Files/
    - Archives/
    - Backups/
  - System/
    - Config/
    - Logs/
    - Cache/

# Generic device information
device_info={{
    "type": "unknown_storage",
    "interface": "{device.connection_type}",
    "capacity_gb": {device.capacity // 1000000000},
    "status": "active"
}}

# Generic data patterns
data_pattern_001: structured_data_block
data_pattern_002: unstructured_content
data_pattern_003: binary_information

# Generic data blocks
{"GENERIC_DATA_" * 300}

# End of sample data for {device.device_id}
"""


def main():
    """Main function for standalone execution."""
    print("🎯 SAMPLE IT ASSETS GENERATOR")
    print("=" * 50)
    
    generator = SampleITAssetsGenerator()
    demo_env = generator.generate_complete_demo_environment()
    
    print(f"\n📊 Demo Environment Summary:")
    print(f"  Total Devices: {demo_env['total_devices']}")
    print(f"  Scenarios: {len(demo_env['scenarios'])}")
    print(f"  Output Directory: {demo_env['output_directory']}")
    
    print(f"\n🎭 Available Scenarios:")
    for scenario_name, devices in demo_env['scenarios'].items():
        device_counts = {}
        for device in devices:
            device_type = device.device_type.value
            device_counts[device_type] = device_counts.get(device_type, 0) + 1
        
        counts_str = ", ".join([f"{count} {dtype}" for dtype, count in device_counts.items()])
        print(f"  {scenario_name}: {counts_str}")
    
    print(f"\n✅ Sample IT assets ready for demonstration!")
    return 0


if __name__ == "__main__":
    sys.exit(main())