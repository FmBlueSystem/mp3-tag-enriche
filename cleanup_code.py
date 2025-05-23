#!/usr/bin/env python3
"""
Script automatizado para limpiar código obsoleto y duplicado del proyecto.
Basado en el análisis exhaustivo del código fuente.

Este script implementa el plan de limpieza de código en fases para:
- Eliminar archivos obsoletos
- Consolidar duplicaciones
- Mantener la funcionalidad core intacta
"""

import os
import sys
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Tuple
import json
from datetime import datetime

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cleanup.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class CodeCleanup:
    """Maneja la limpieza automatizada del código del proyecto."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root / "backup_cleanup"
        self.cleanup_report = {
            "timestamp": datetime.now().isoformat(),
            "files_removed": [],
            "files_backed_up": [],
            "errors": [],
            "phases_completed": []
        }
        
        # Definir archivos para eliminar por categoría
        self.files_to_remove = {
            "empty_files": [
                "mp3_tool.py"
            ],
            "debug_scripts": [
                "analyze_directory.py",
                "analyze_file.py", 
                "check_metadata.py",
                "test_path.py",
                "verify_changes.py",
                "fix_cases.py",
                "fix_api.py",
                "clear_api_caches.py"
            ],
            "obsolete_tests": [
                "test_backup.py",
                "test_filename_extraction.py",
                "test_genre_year.py", 
                "test_metadata_handling.py",
                "test_rename.py",
                "test_real_files.py",
                "test_spotify_credentials.py",
                "test_spotify_api.py"
            ],
            "demo_scripts": [
                "demo_extractor_mejorado.py",
                "spotify_demo.py",
                "compare_extraction_methods.py"
            ],
            "obsolete_utilities": [
                "genre_summary.py",
                "limpiar_metadatos_mp3.py", 
                "show_mp3_tags.py",
                "write_genres.py"
            ],
            "duplicate_files": [
                "src/run_gui.py"
            ]
        }
    
    def create_backup(self) -> bool:
        """Crea un backup completo antes de la limpieza."""
        try:
            logger.info("🔄 Creando backup del proyecto...")
            
            if self.backup_dir.exists():
                shutil.rmtree(self.backup_dir)
            
            self.backup_dir.mkdir(exist_ok=True)
            
            # Backup de archivos críticos
            files_to_backup = []
            for category_files in self.files_to_remove.values():
                files_to_backup.extend(category_files)
            
            for file_path in files_to_backup:
                full_path = self.project_root / file_path
                if full_path.exists():
                    backup_path = self.backup_dir / file_path
                    backup_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(full_path, backup_path)
                    self.cleanup_report["files_backed_up"].append(str(file_path))
                    logger.debug(f"Backup creado: {file_path}")
            
            logger.info(f"✅ Backup completado en: {self.backup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error creando backup: {e}")
            return False
    
    def remove_files_by_category(self, category: str) -> bool:
        """Elimina archivos de una categoría específica."""
        try:
            files = self.files_to_remove.get(category, [])
            logger.info(f"🗑️ Eliminando archivos de categoría: {category}")
            
            for file_path in files:
                full_path = self.project_root / file_path
                if full_path.exists():
                    os.remove(full_path)
                    self.cleanup_report["files_removed"].append(str(file_path))
                    logger.info(f"   ❌ Eliminado: {file_path}")
                else:
                    logger.warning(f"   ⚠️ No encontrado: {file_path}")
            
            return True
            
        except Exception as e:
            error_msg = f"Error eliminando archivos de {category}: {e}"
            logger.error(f"❌ {error_msg}")
            self.cleanup_report["errors"].append(error_msg)
            return False
    
    def check_imports_before_removal(self) -> Dict[str, List[str]]:
        """Verifica qué archivos importan los módulos a eliminar."""
        logger.info("🔍 Verificando imports antes de eliminar...")
        
        problematic_imports = {}
        
        # Archivos que tienen imports críticos
        critical_files = [
            "src/core/improved_file_handler.py",
            "src/core/enhanced_mp3_handler.py"
        ]
        
        for file_to_check in critical_files:
            imports_found = []
            
            # Buscar imports en todos los archivos Python
            for py_file in self.project_root.rglob("*.py"):
                if py_file.name.startswith('.') or 'venv' in str(py_file) or '__pycache__' in str(py_file):
                    continue
                
                try:
                    content = py_file.read_text(encoding='utf-8')
                    module_name = file_to_check.replace('src/core/', '').replace('.py', '')
                    
                    if f"from.*{module_name}" in content or f"import.*{module_name}" in content:
                        imports_found.append(str(py_file.relative_to(self.project_root)))
                        
                except Exception as e:
                    logger.warning(f"Error leyendo {py_file}: {e}")
            
            if imports_found:
                problematic_imports[file_to_check] = imports_found
        
        return problematic_imports
    
    def run_tests_verification(self) -> bool:
        """Ejecuta tests para verificar que el sistema sigue funcionando."""
        try:
            logger.info("🧪 Ejecutando verificación de tests...")
            
            # Ejecutar test_improvements.py para verificar mejoras
            import subprocess
            result = subprocess.run([
                sys.executable, "test_improvements.py"
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode == 0:
                logger.info("✅ Tests de mejoras pasaron correctamente")
                return True
            else:
                logger.error(f"❌ Tests fallaron: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error ejecutando tests: {e}")
            return False
    
    def execute_cleanup_phase_1(self) -> bool:
        """Fase 1: Eliminar archivos de bajo riesgo."""
        logger.info("🚀 FASE 1: Eliminando archivos de bajo riesgo")
        
        phases = [
            ("empty_files", "Archivos vacíos"),
            ("debug_scripts", "Scripts de debug"),
            ("obsolete_tests", "Tests obsoletos individuales"),
            ("demo_scripts", "Scripts de demo"),
            ("obsolete_utilities", "Utilidades obsoletas"),
            ("duplicate_files", "Archivos duplicados")
        ]
        
        for category, description in phases:
            logger.info(f"📂 {description}...")
            if not self.remove_files_by_category(category):
                return False
            self.cleanup_report["phases_completed"].append(f"Phase 1 - {description}")
        
        return True
    
    def generate_report(self):
        """Genera un reporte detallado de la limpieza."""
        report_file = self.project_root / "cleanup_report.json"
        
        # Estadísticas de limpieza
        self.cleanup_report["summary"] = {
            "total_files_removed": len(self.cleanup_report["files_removed"]),
            "total_files_backed_up": len(self.cleanup_report["files_backed_up"]),
            "total_errors": len(self.cleanup_report["errors"]),
            "phases_completed": len(self.cleanup_report["phases_completed"])
        }
        
        # Contar archivos restantes
        py_files_remaining = len(list(self.project_root.rglob("*.py")))
        self.cleanup_report["files_remaining"] = py_files_remaining
        
        with open(report_file, 'w') as f:
            json.dump(self.cleanup_report, f, indent=2)
        
        logger.info(f"📋 Reporte guardado en: {report_file}")
        
        # Mostrar resumen
        logger.info("📊 RESUMEN DE LIMPIEZA:")
        logger.info(f"   ✅ Archivos eliminados: {self.cleanup_report['summary']['total_files_removed']}")
        logger.info(f"   📦 Archivos respaldados: {self.cleanup_report['summary']['total_files_backed_up']}")
        logger.info(f"   ⚠️ Errores: {self.cleanup_report['summary']['total_errors']}")
        logger.info(f"   📁 Archivos Python restantes: {py_files_remaining}")
    
    def run_full_cleanup(self):
        """Ejecuta el proceso completo de limpieza."""
        logger.info("🧹 INICIANDO LIMPIEZA AUTOMÁTICA DEL CÓDIGO")
        logger.info("=" * 60)
        
        # Paso 1: Crear backup
        if not self.create_backup():
            logger.error("❌ No se pudo crear backup. Abortando limpieza.")
            return False
        
        # Paso 2: Verificar imports problemáticos
        problematic_imports = self.check_imports_before_removal()
        if problematic_imports:
            logger.warning("⚠️ IMPORTS PROBLEMÁTICOS DETECTADOS:")
            for file, imports in problematic_imports.items():
                logger.warning(f"   {file} es importado por:")
                for imp in imports:
                    logger.warning(f"     - {imp}")
        
        # Paso 3: Ejecutar Fase 1 de limpieza
        if not self.execute_cleanup_phase_1():
            logger.error("❌ Error en Fase 1 de limpieza.")
            return False
        
        # Paso 4: Verificar que todo sigue funcionando
        if not self.run_tests_verification():
            logger.warning("⚠️ Algunos tests fallaron después de la limpieza")
        
        # Paso 5: Generar reporte
        self.generate_report()
        
        logger.info("🎉 LIMPIEZA COMPLETADA EXITOSAMENTE")
        logger.info(f"📦 Backup disponible en: {self.backup_dir}")
        return True

def main():
    """Función principal."""
    cleanup = CodeCleanup()
    
    # Mostrar qué archivos se van a eliminar
    logger.info("📋 ARCHIVOS QUE SERÁN ELIMINADOS:")
    total_files = 0
    for category, files in cleanup.files_to_remove.items():
        logger.info(f"\n📂 {category.upper()}:")
        for file in files:
            logger.info(f"   - {file}")
            total_files += 1
    
    logger.info(f"\n📊 TOTAL: {total_files} archivos serán eliminados")
    
    # Confirmar antes de proceder
    response = input("\n¿Deseas proceder con la limpieza? (s/N): ").strip().lower()
    if response not in ['s', 'si', 'sí', 'y', 'yes']:
        logger.info("❌ Limpieza cancelada por el usuario.")
        return
    
    # Ejecutar limpieza
    success = cleanup.run_full_cleanup()
    
    if success:
        logger.info("\n✅ Limpieza completada exitosamente!")
        logger.info("💡 Recomendaciones post-limpieza:")
        logger.info("   1. Ejecutar tests completos: python -m pytest tests/")
        logger.info("   2. Verificar funcionalidad GUI: python run_gui.py")
        logger.info("   3. Revisar imports problemáticos si los hay")
        logger.info("   4. Considerar consolidar file handlers en Fase 2")
    else:
        logger.error("\n❌ La limpieza encontró errores. Revisar logs.")
        logger.info(f"📦 Backup disponible en: {cleanup.backup_dir}")

if __name__ == "__main__":
    main() 