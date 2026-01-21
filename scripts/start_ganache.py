#!/usr/bin/env python3
"""
Ganache Startup Script

This script starts a local Ganache blockchain instance with the correct
configuration for the secure data wiping project.

Requirements:
- Ganache CLI installed: npm install -g ganache-cli
- Or Ganache GUI application

Usage:
    python scripts/start_ganache.py
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path
from typing import List, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from secure_data_wiping.utils.logging_config import get_component_logger


class GanacheManager:
    """
    Manages Ganache blockchain instance for development and testing.
    
    This class handles:
    1. Starting Ganache with appropriate configuration
    2. Checking if Ganache is already running
    3. Stopping Ganache when needed
    4. Providing connection information
    """
    
    def __init__(self):
        """Initialize the Ganache manager."""
        self.logger = get_component_logger('ganache_manager')
        self.ganache_process = None
        self.config = self._get_ganache_config()
        
    def _get_ganache_config(self) -> dict:
        """
        Get Ganache configuration for the project.
        
        Returns:
            dict: Ganache configuration parameters
        """
        return {
            'host': '127.0.0.1',
            'port': 8545,
            'network_id': 1337,
            'accounts': 10,
            'ether': 100,
            'mnemonic': 'secure data wiping blockchain audit trail final year project demo',
            'gas_limit': 6721975,
            'gas_price': 20000000000,  # 20 gwei
            'block_time': 0,  # Auto-mine
            'deterministic': True,
            'verbose': True
        }
    
    def check_ganache_cli_installed(self) -> bool:
        """
        Check if Ganache CLI is installed.
        
        Returns:
            bool: True if Ganache CLI is available, False otherwise
        """
        try:
            result = subprocess.run(
                ['ganache-cli', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                version = result.stdout.strip()
                self.logger.info(f"Ganache CLI found: {version}")
                return True
            else:
                self.logger.warning("Ganache CLI not found")
                return False
                
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            self.logger.warning(f"Ganache CLI check failed: {e}")
            return False
    
    def is_ganache_running(self) -> bool:
        """
        Check if Ganache is already running on the configured port.
        
        Returns:
            bool: True if Ganache is running, False otherwise
        """
        try:
            import requests
            
            url = f"http://{self.config['host']}:{self.config['port']}"
            
            # Try to make a simple JSON-RPC call
            payload = {
                "jsonrpc": "2.0",
                "method": "eth_blockNumber",
                "params": [],
                "id": 1
            }
            
            response = requests.post(url, json=payload, timeout=5)
            
            if response.status_code == 200:
                self.logger.info(f"Ganache is already running on {url}")
                return True
            else:
                return False
                
        except Exception as e:
            self.logger.debug(f"Ganache not running: {e}")
            return False
    
    def build_ganache_command(self) -> List[str]:
        """
        Build the Ganache CLI command with configuration.
        
        Returns:
            List[str]: Command line arguments for Ganache
        """
        cmd = [
            'ganache-cli',
            '--host', self.config['host'],
            '--port', str(self.config['port']),
            '--networkId', str(self.config['network_id']),
            '--accounts', str(self.config['accounts']),
            '--defaultBalanceEther', str(self.config['ether']),
            '--mnemonic', self.config['mnemonic'],
            '--gasLimit', str(self.config['gas_limit']),
            '--gasPrice', str(self.config['gas_price']),
            '--blockTime', str(self.config['block_time']),
            '--deterministic'
        ]
        
        if self.config['verbose']:
            cmd.append('--verbose')
        
        return cmd
    
    def start_ganache(self) -> bool:
        """
        Start Ganache blockchain instance.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        try:
            # Check if already running
            if self.is_ganache_running():
                self.logger.info("Ganache is already running")
                return True
            
            # Check if Ganache CLI is installed
            if not self.check_ganache_cli_installed():
                self.logger.error("Ganache CLI is not installed")
                self.logger.error("Please install it with: npm install -g ganache-cli")
                return False
            
            # Build command
            cmd = self.build_ganache_command()
            
            self.logger.info("Starting Ganache blockchain...")
            self.logger.info(f"Command: {' '.join(cmd)}")
            
            # Start Ganache process
            self.ganache_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Wait a moment for startup
            time.sleep(3)
            
            # Check if process is still running
            if self.ganache_process.poll() is None:
                # Verify connection
                if self.is_ganache_running():
                    self.logger.info("Ganache started successfully!")
                    self._log_ganache_info()
                    return True
                else:
                    self.logger.error("Ganache started but connection failed")
                    return False
            else:
                # Process terminated
                stdout, stderr = self.ganache_process.communicate()
                self.logger.error(f"Ganache failed to start")
                self.logger.error(f"stdout: {stdout}")
                self.logger.error(f"stderr: {stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to start Ganache: {e}")
            return False
    
    def stop_ganache(self) -> bool:
        """
        Stop the Ganache blockchain instance.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        try:
            if self.ganache_process and self.ganache_process.poll() is None:
                self.logger.info("Stopping Ganache...")
                self.ganache_process.terminate()
                
                # Wait for graceful shutdown
                try:
                    self.ganache_process.wait(timeout=10)
                    self.logger.info("Ganache stopped successfully")
                    return True
                except subprocess.TimeoutExpired:
                    self.logger.warning("Ganache didn't stop gracefully, forcing...")
                    self.ganache_process.kill()
                    self.ganache_process.wait()
                    self.logger.info("Ganache force stopped")
                    return True
            else:
                self.logger.info("Ganache is not running")
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to stop Ganache: {e}")
            return False
    
    def _log_ganache_info(self):
        """Log Ganache connection information."""
        url = f"http://{self.config['host']}:{self.config['port']}"
        
        self.logger.info("=" * 50)
        self.logger.info("🔗 Ganache Blockchain Information")
        self.logger.info("=" * 50)
        self.logger.info(f"📡 RPC URL: {url}")
        self.logger.info(f"🌐 Network ID: {self.config['network_id']}")
        self.logger.info(f"👥 Accounts: {self.config['accounts']}")
        self.logger.info(f"💰 Default Balance: {self.config['ether']} ETH")
        self.logger.info(f"🔑 Mnemonic: {self.config['mnemonic']}")
        self.logger.info(f"⛽ Gas Limit: {self.config['gas_limit']:,}")
        self.logger.info(f"💸 Gas Price: {self.config['gas_price']:,} wei")
        self.logger.info("=" * 50)
    
    def get_connection_info(self) -> dict:
        """
        Get connection information for the running Ganache instance.
        
        Returns:
            dict: Connection information
        """
        return {
            'url': f"http://{self.config['host']}:{self.config['port']}",
            'host': self.config['host'],
            'port': self.config['port'],
            'network_id': self.config['network_id'],
            'chain_id': self.config['network_id']
        }
    
    def save_connection_config(self) -> bool:
        """
        Save Ganache connection configuration to file.
        
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            config_dir = project_root / "config"
            config_dir.mkdir(exist_ok=True)
            
            connection_info = self.get_connection_info()
            config_path = config_dir / "ganache_config.json"
            
            with open(config_path, 'w') as f:
                json.dump(connection_info, f, indent=2)
            
            self.logger.info(f"Ganache configuration saved to: {config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save Ganache configuration: {e}")
            return False


def main():
    """Main function to start Ganache."""
    print("🚀 Ganache Blockchain Startup Script")
    print("=" * 50)
    
    # Create Ganache manager
    ganache = GanacheManager()
    
    try:
        # Start Ganache
        if ganache.start_ganache():
            # Save configuration
            ganache.save_connection_config()
            
            print("\n✅ Ganache started successfully!")
            print("🔗 Connection Information:")
            
            conn_info = ganache.get_connection_info()
            print(f"   📡 RPC URL: {conn_info['url']}")
            print(f"   🌐 Network ID: {conn_info['network_id']}")
            print(f"   ⛓️  Chain ID: {conn_info['chain_id']}")
            
            print("\n🎯 Next Steps:")
            print("   1. Deploy smart contract: python scripts/deploy_contract.py")
            print("   2. Run tests: python -m pytest tests/")
            print("   3. Start main application: python main.py")
            
            print("\n⚠️  Keep this terminal open to maintain the blockchain")
            print("   Press Ctrl+C to stop Ganache")
            
            # Keep running until interrupted
            try:
                while ganache.ganache_process and ganache.ganache_process.poll() is None:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Stopping Ganache...")
                ganache.stop_ganache()
                print("✅ Ganache stopped successfully")
                return 0
            
        else:
            print("\n❌ Failed to start Ganache!")
            print("🔧 Please check the logs and try again.")
            print("\n💡 Troubleshooting:")
            print("   1. Make sure Node.js is installed")
            print("   2. Install Ganache CLI: npm install -g ganache-cli")
            print("   3. Check if port 8545 is available")
            return 1
            
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        ganache.stop_ganache()
        return 0
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        ganache.stop_ganache()
        return 1


if __name__ == "__main__":
    sys.exit(main())