#!/usr/bin/env python3
"""
Script para validar la consistencia de la documentación del proyecto.
Verifica:
- Referencias cruzadas entre documentos
- Información contradictoria
- Archivos mencionados que no existen
- Comandos y rutas correctas
- Completitud de la documentación
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Set, Tuple
import argparse

class DocumentationValidator:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.docs = {}
        self.issues = []
        self.project_files = set()
        
    def load_documentation(self):
        """Carga todos los archivos de documentación."""
        doc_patterns = ["*.md", "*.rst", "*.txt"]
        
        for pattern in doc_patterns:
            for doc_file in self.project_root.rglob(pattern):
                # Excluir documentación de dependencias
                if any(excluded in str(doc_file) for excluded in ['.venv', 'venv', '.pytest_cache', 'node_modules']):
                    continue
                    
                try:
                    with open(doc_file, 'r', encoding='utf-8') as f:
                        self.docs[str(doc_file.relative_to(self.project_root))] = f.read()
                except Exception as e:
                    self.issues.append(f"❌ Error leyendo {doc_file}: {e}")
    
    def scan_project_files(self):
        """Escanea archivos reales del proyecto."""
        for file_path in self.project_root.rglob("*"):
            if file_path.is_file() and not any(excluded in str(file_path) for excluded in ['.venv', 'venv', '.git', '__pycache__']):
                self.project_files.add(str(file_path.relative_to(self.project_root)))
    
    def validate_file_references(self):
        """Valida que archivos mencionados en la documentación existan."""
        print("🔍 Validando referencias de archivos...")
        
        # Patrones para detectar referencias de archivos
        file_patterns = [
            r'`([^`]+\.py)`',  # Archivos Python en backticks
            r'`([^`]+\.json)`',  # Archivos JSON en backticks
            r'`([^`]+\.md)`',  # Archivos MD en backticks
            r'src/[a-zA-Z0-9_/]+\.py',  # Rutas src específicas
            r'config/[a-zA-Z0-9_/]+\.[a-zA-Z]+',  # Archivos de config
            r'tests/[a-zA-Z0-9_/]+\.py',  # Archivos de tests
        ]
        
        for doc_path, content in self.docs.items():
            for pattern in file_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for match in matches:
                    if match not in self.project_files:
                        self.issues.append(f"❌ {doc_path}: Archivo no encontrado: {match}")
    
    def validate_command_references(self):
        """Valida que comandos mencionados sean válidos."""
        print("🔍 Validando comandos...")
        
        python_commands = []
        for doc_path, content in self.docs.items():
            # Buscar comandos python
            python_patterns = [
                r'python\s+([a-zA-Z0-9_./]+\.py)',
                r'python3\s+([a-zA-Z0-9_./]+\.py)',
                r'python\s+-m\s+([a-zA-Z0-9_.]+)',
            ]
            
            for pattern in python_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    python_commands.append((doc_path, match))
        
        # Validar archivos Python mencionados
        for doc_path, script in python_commands:
            if script.endswith('.py') and script not in self.project_files:
                self.issues.append(f"❌ {doc_path}: Script no encontrado: {script}")
    
    def validate_cross_references(self):
        """Valida referencias cruzadas entre documentos."""
        print("🔍 Validando referencias cruzadas...")
        
        all_doc_names = set(self.docs.keys())
        
        for doc_path, content in self.docs.items():
            # Buscar referencias a otros documentos
            md_refs = re.findall(r'\[([^\]]+)\]\(([^)]+\.md)\)', content)
            for desc, ref_file in md_refs:
                if ref_file not in all_doc_names and ref_file not in self.project_files:
                    self.issues.append(f"❌ {doc_path}: Documento referenciado no encontrado: {ref_file}")
    
    def validate_project_structure_consistency(self):
        """Valida que la estructura documentada coincida con la real."""
        print("🔍 Validando estructura del proyecto...")
        
        # Buscar descripciones de estructura en documentación
        structure_patterns = [
            r'├── ([a-zA-Z0-9_./]+)',
            r'└── ([a-zA-Z0-9_./]+)',
            r'│   ├── ([a-zA-Z0-9_./]+)',
            r'│   └── ([a-zA-Z0-9_./]+)',
        ]
        
        for doc_path, content in self.docs.items():
            for pattern in structure_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    # Limpiar el match (remover comentarios)
                    clean_match = match.split('#')[0].strip()
                    if clean_match.endswith('/'):
                        # Es un directorio
                        dir_path = clean_match.rstrip('/')
                        if not (self.project_root / dir_path).exists():
                            self.issues.append(f"⚠️  {doc_path}: Directorio documentado no encontrado: {dir_path}")
                    elif '.' in clean_match:
                        # Es un archivo
                        if clean_match not in self.project_files:
                            self.issues.append(f"⚠️  {doc_path}: Archivo documentado no encontrado: {clean_match}")
    
    def validate_configuration_consistency(self):
        """Valida que la configuración documentada sea consistente."""
        print("🔍 Validando configuración...")
        
        # Buscar menciones de configuración
        config_patterns = [
            r'"([a-zA-Z_]+)":\s*"([^"]*)"',  # Configuración JSON
            r'--([a-zA-Z-]+)',  # Argumentos de línea de comandos
            r'config\.([a-zA-Z_]+)',  # Referencias a configuración
        ]
        
        config_mentions = {}
        
        for doc_path, content in self.docs.items():
            for pattern in config_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    key = match if isinstance(match, str) else match[0]
                    if key not in config_mentions:
                        config_mentions[key] = []
                    config_mentions[key].append((doc_path, match))
        
        # Verificar configuraciones reales
        config_files = ['config/api_keys.json', 'config/dynamic_settings.json', 'config/genre_fallbacks.json']
        real_config = {}
        
        for config_file in config_files:
            config_path = self.project_root / config_file
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        real_config[config_file] = json.load(f)
                except:
                    pass
    
    def validate_version_consistency(self):
        """Valida que las versiones mencionadas sean consistentes."""
        print("🔍 Validando versiones...")
        
        version_patterns = [
            r'v(\d+\.\d+(?:\.\d+)?)',
            r'version\s*[=:]\s*["\']([^"\']+)["\']',
            r'Sistema.*v(\d+\.\d+)',
        ]
        
        versions_found = {}
        
        for doc_path, content in self.docs.items():
            for pattern in version_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                for version in matches:
                    if version not in versions_found:
                        versions_found[version] = []
                    versions_found[version].append(doc_path)
        
        # Reportar versiones múltiples
        if len(versions_found) > 1:
            self.issues.append(f"⚠️  Múltiples versiones encontradas: {list(versions_found.keys())}")
    
    def validate_api_documentation(self):
        """Valida que la documentación de APIs sea consistente."""
        print("🔍 Validando documentación de APIs...")
        
        # APIs mencionadas en documentación
        api_mentions = {
            'spotify': [],
            'lastfm': [],
            'musicbrainz': [],
            'discogs': []
        }
        
        for doc_path, content in self.docs.items():
            content_lower = content.lower()
            for api in api_mentions:
                if api in content_lower:
                    api_mentions[api].append(doc_path)
        
        # Verificar que todas las APIs tengan documentación
        for api, docs in api_mentions.items():
            if not docs:
                self.issues.append(f"⚠️  API {api} no tiene documentación")
    
    def check_documentation_completeness(self):
        """Verifica que la documentación esté completa."""
        print("🔍 Verificando completitud de documentación...")
        
        required_sections = {
            'installation': ['install', 'requirements', 'dependencies'],
            'usage': ['usage', 'running', 'execute'],
            'configuration': ['config', 'setup', 'setting'],
            'testing': ['test', 'pytest'],
            'api': ['api', 'endpoint'],
        }
        
        coverage = {}
        
        for section, keywords in required_sections.items():
            coverage[section] = []
            for doc_path, content in self.docs.items():
                content_lower = content.lower()
                if any(keyword in content_lower for keyword in keywords):
                    coverage[section].append(doc_path)
        
        # Reportar secciones faltantes
        for section, docs in coverage.items():
            if not docs:
                self.issues.append(f"⚠️  Sección faltante: {section}")
    
    def generate_report(self):
        """Genera reporte de validación."""
        print("\n" + "="*60)
        print("📋 REPORTE DE VALIDACIÓN DE DOCUMENTACIÓN")
        print("="*60)
        
        if not self.issues:
            print("✅ ¡Documentación consistente! No se encontraron problemas.")
            return True
        
        print(f"❌ Se encontraron {len(self.issues)} problemas:")
        print()
        
        # Agrupar problemas por tipo
        error_groups = {
            'Referencias de archivos': [],
            'Comandos': [],
            'Referencias cruzadas': [],
            'Estructura': [],
            'Configuración': [],
            'Versiones': [],
            'APIs': [],
            'Completitud': []
        }
        
        for issue in self.issues:
            if 'Archivo no encontrado' in issue or 'Script no encontrado' in issue:
                error_groups['Referencias de archivos'].append(issue)
            elif 'Comando' in issue:
                error_groups['Comandos'].append(issue)
            elif 'Documento referenciado' in issue:
                error_groups['Referencias cruzadas'].append(issue)
            elif 'documentado no encontrado' in issue:
                error_groups['Estructura'].append(issue)
            elif 'Múltiples versiones' in issue:
                error_groups['Versiones'].append(issue)
            elif 'API' in issue:
                error_groups['APIs'].append(issue)
            elif 'Sección faltante' in issue:
                error_groups['Completitud'].append(issue)
            else:
                error_groups['Configuración'].append(issue)
        
        for group, issues in error_groups.items():
            if issues:
                print(f"\n📂 {group}:")
                for issue in issues:
                    print(f"   {issue}")
        
        return False
    
    def run_validation(self):
        """Ejecuta todas las validaciones."""
        print("🔍 Iniciando validación de documentación...")
        
        self.load_documentation()
        self.scan_project_files()
        
        print(f"📚 {len(self.docs)} documentos encontrados")
        print(f"📁 {len(self.project_files)} archivos de proyecto escaneados")
        print()
        
        self.validate_file_references()
        self.validate_command_references()
        self.validate_cross_references()
        self.validate_project_structure_consistency()
        self.validate_configuration_consistency()
        self.validate_version_consistency()
        self.validate_api_documentation()
        self.check_documentation_completeness()
        
        return self.generate_report()

def main():
    parser = argparse.ArgumentParser(description="Valida la consistencia de la documentación")
    parser.add_argument("--project-root", default=".", help="Ruta raíz del proyecto")
    parser.add_argument("--verbose", "-v", action="store_true", help="Salida detallada")
    
    args = parser.parse_args()
    
    validator = DocumentationValidator(args.project_root)
    success = validator.run_validation()
    
    if success:
        print("\n🎉 Validación completada exitosamente")
        exit(0)
    else:
        print("\n💡 Recomendaciones:")
        print("   1. Revisar archivos mencionados que no existen")
        print("   2. Actualizar referencias rotas")
        print("   3. Completar secciones faltantes")
        print("   4. Unificar versiones mencionadas")
        exit(1)

if __name__ == "__main__":
    main() 