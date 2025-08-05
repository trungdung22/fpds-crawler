"""
Config Manager Module
Manages extraction configurations for the intelligent crawling framework
"""

import json
import os
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    """
    Manages extraction configurations for intelligent web crawling
    Handles saving, loading, and versioning of extraction configs
    """
    
    def __init__(self, config_dir: str = "lib/configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Config metadata file
        self.metadata_file = self.config_dir / "config_metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load configuration metadata"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load config metadata: {e}")
        
        return {
            'configs': {},
            'last_updated': datetime.now().isoformat(),
            'version': '1.0'
        }
    
    def _save_metadata(self):
        """Save configuration metadata"""
        try:
            self.metadata['last_updated'] = datetime.now().isoformat()
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save config metadata: {e}")
    
    def save_config(self, config: Dict[str, Any], name: str, description: str = "", 
                   domain: str = "", tags: List[str] = None) -> str:
        """
        Save extraction configuration
        
        Args:
            config: Extraction configuration dictionary
            name: Configuration name
            description: Configuration description
            domain: Target domain/website
            tags: List of tags for categorization
            
        Returns:
            Configuration file path
        """
        # Validate config
        if not self._validate_config(config):
            raise ValueError("Invalid configuration structure")
        
        # Create config filename
        safe_name = self._sanitize_filename(name)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{safe_name}_{timestamp}.json"
        config_path = self.config_dir / filename
        
        # Add metadata to config
        config_with_metadata = {
            'config': config,
            'metadata': {
                'name': name,
                'description': description,
                'domain': domain,
                'tags': tags or [],
                'created_at': datetime.now().isoformat(),
                'version': '1.0',
                'fields': list(config.get('selectors', {}).keys())
            }
        }
        
        # Save config file
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_with_metadata, f, indent=2, ensure_ascii=False)
            
            # Update metadata
            self.metadata['configs'][name] = {
                'file_path': str(config_path),
                'description': description,
                'domain': domain,
                'tags': tags or [],
                'created_at': config_with_metadata['metadata']['created_at'],
                'fields': config_with_metadata['metadata']['fields'],
                'version': '1.0'
            }
            
            self._save_metadata()
            
            logger.info(f"Configuration saved: {config_path}")
            return str(config_path)
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")
            raise
    
    def load_config(self, name: str) -> Dict[str, Any]:
        """
        Load extraction configuration by name
        
        Args:
            name: Configuration name
            
        Returns:
            Configuration dictionary
        """
        if name not in self.metadata['configs']:
            raise ValueError(f"Configuration '{name}' not found")
        
        config_info = self.metadata['configs'][name]
        config_path = Path(config_info['file_path'])
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            logger.info(f"Configuration loaded: {name}")
            return config_data['config']
            
        except Exception as e:
            logger.error(f"Failed to load configuration '{name}': {e}")
            raise
    
    def load_config_from_file(self, config_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load configuration from specific file path
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        config_path = Path(config_path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Handle both old and new format
            if 'config' in config_data:
                return config_data['config']
            else:
                return config_data
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {config_path}: {e}")
            raise
    
    def list_configs(self, domain: str = None, tags: List[str] = None) -> List[Dict[str, Any]]:
        """
        List available configurations
        
        Args:
            domain: Filter by domain
            tags: Filter by tags
            
        Returns:
            List of configuration information
        """
        configs = []
        
        for name, info in self.metadata['configs'].items():
            # Apply filters
            if domain and info.get('domain') != domain:
                continue
            
            if tags:
                config_tags = set(info.get('tags', []))
                if not any(tag in config_tags for tag in tags):
                    continue
            
            configs.append({
                'name': name,
                **info
            })
        
        return sorted(configs, key=lambda x: x['created_at'], reverse=True)
    
    def delete_config(self, name: str) -> bool:
        """
        Delete configuration
        
        Args:
            name: Configuration name
            
        Returns:
            True if deleted successfully
        """
        if name not in self.metadata['configs']:
            logger.warning(f"Configuration '{name}' not found")
            return False
        
        config_info = self.metadata['configs'][name]
        config_path = Path(config_info['file_path'])
        
        try:
            # Delete config file
            if config_path.exists():
                config_path.unlink()
            
            # Remove from metadata
            del self.metadata['configs'][name]
            self._save_metadata()
            
            logger.info(f"Configuration deleted: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete configuration '{name}': {e}")
            return False
    
    def update_config(self, name: str, config: Dict[str, Any], description: str = None) -> bool:
        """
        Update existing configuration
        
        Args:
            name: Configuration name
            config: Updated configuration
            description: Updated description (optional)
            
        Returns:
            True if updated successfully
        """
        if name not in self.metadata['configs']:
            logger.warning(f"Configuration '{name}' not found")
            return False
        
        if not self._validate_config(config):
            raise ValueError("Invalid configuration structure")
        
        config_info = self.metadata['configs'][name]
        config_path = Path(config_info['file_path'])
        
        try:
            # Load existing config data
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # Update config
            config_data['config'] = config
            
            # Update metadata
            if description:
                config_data['metadata']['description'] = description
            
            config_data['metadata']['updated_at'] = datetime.now().isoformat()
            config_data['metadata']['fields'] = list(config.get('selectors', {}).keys())
            
            # Save updated config
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            # Update metadata
            self.metadata['configs'][name]['description'] = description or config_info['description']
            self.metadata['configs'][name]['fields'] = config_data['metadata']['fields']
            self._save_metadata()
            
            logger.info(f"Configuration updated: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update configuration '{name}': {e}")
            return False
    
    def get_config_stats(self) -> Dict[str, Any]:
        """
        Get statistics about stored configurations
        
        Returns:
            Statistics dictionary
        """
        configs = self.metadata['configs']
        
        if not configs:
            return {
                'total_configs': 0,
                'domains': [],
                'tags': [],
                'fields': []
            }
        
        # Collect statistics
        domains = set()
        all_tags = set()
        all_fields = set()
        
        for info in configs.values():
            if info.get('domain'):
                domains.add(info['domain'])
            
            all_tags.update(info.get('tags', []))
            all_fields.update(info.get('fields', []))
        
        return {
            'total_configs': len(configs),
            'domains': list(domains),
            'tags': list(all_tags),
            'fields': list(all_fields),
            'recent_configs': sorted(
                [{'name': name, **info} for name, info in configs.items()],
                key=lambda x: x['created_at'],
                reverse=True
            )[:5]
        }
    
    def export_configs(self, output_path: Union[str, Path], format: str = 'json'):
        """
        Export all configurations
        
        Args:
            output_path: Output file path
            format: Export format ('json' or 'zip')
        """
        output_path = Path(output_path)
        
        if format.lower() == 'json':
            # Export as single JSON file
            export_data = {
                'metadata': self.metadata,
                'configs': {}
            }
            
            for name, info in self.metadata['configs'].items():
                try:
                    config = self.load_config(name)
                    export_data['configs'][name] = {
                        'config': config,
                        'info': info
                    }
                except Exception as e:
                    logger.warning(f"Failed to load config '{name}' for export: {e}")
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        elif format.lower() == 'zip':
            # Export as ZIP archive
            import zipfile
            
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add metadata
                zipf.writestr('metadata.json', json.dumps(self.metadata, indent=2))
                
                # Add config files
                for name, info in self.metadata['configs'].items():
                    config_path = Path(info['file_path'])
                    if config_path.exists():
                        zipf.write(config_path, config_path.name)
        
        logger.info(f"Configurations exported to: {output_path}")
    
    def import_configs(self, import_path: Union[str, Path], format: str = 'json'):
        """
        Import configurations
        
        Args:
            import_path: Import file path
            format: Import format ('json' or 'zip')
        """
        import_path = Path(import_path)
        
        if not import_path.exists():
            raise FileNotFoundError(f"Import file not found: {import_path}")
        
        if format.lower() == 'json':
            # Import from JSON file
            with open(import_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            imported_count = 0
            for name, data in import_data.get('configs', {}).items():
                try:
                    config = data['config']
                    info = data['info']
                    
                    # Save config
                    self.save_config(
                        config=config,
                        name=name,
                        description=info.get('description', ''),
                        domain=info.get('domain', ''),
                        tags=info.get('tags', [])
                    )
                    imported_count += 1
                    
                except Exception as e:
                    logger.warning(f"Failed to import config '{name}': {e}")
            
            logger.info(f"Imported {imported_count} configurations")
        
        elif format.lower() == 'zip':
            # Import from ZIP archive
            import zipfile
            
            with zipfile.ZipFile(import_path, 'r') as zipf:
                # Read metadata
                metadata_data = json.loads(zipf.read('metadata.json'))
                
                imported_count = 0
                for name, info in metadata_data.get('configs', {}).items():
                    try:
                        # Extract config file
                        config_filename = Path(info['file_path']).name
                        config_data = json.loads(zipf.read(config_filename))
                        
                        # Save config
                        self.save_config(
                            config=config_data['config'],
                            name=name,
                            description=info.get('description', ''),
                            domain=info.get('domain', ''),
                            tags=info.get('tags', [])
                        )
                        imported_count += 1
                        
                    except Exception as e:
                        logger.warning(f"Failed to import config '{name}': {e}")
                
                logger.info(f"Imported {imported_count} configurations")
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration structure
        
        Args:
            config: Configuration to validate
            
        Returns:
            True if valid
        """
        required_keys = ['selectors', 'confidence_scores', 'fallback_selectors']
        
        for key in required_keys:
            if key not in config:
                logger.error(f"Missing required key: {key}")
                return False
        
        if not isinstance(config['selectors'], dict):
            logger.error("Selectors must be a dictionary")
            return False
        
        return True
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for safe file system usage
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Remove leading/trailing spaces and dots
        filename = filename.strip(' .')
        
        # Limit length
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename 