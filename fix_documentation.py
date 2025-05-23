#!/usr/bin/env python3
"""
Script para corregir automáticamente problemas de consistencia en la documentación.
Aplica correcciones basadas en el análisis de validate_documentation.py
"""

import os
import re
from pathlib import Path
import argparse
import shutil
from datetime import datetime

class DocumentationFixer:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.fixes_applied = []
        self.backup_dir = self.project_root / "backup_docs" / datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def backup_file(self, file_path: Path):
        """Crea respaldo de archivo antes de modificarlo."""
        if not self.backup_dir.exists():
            self.backup_dir.mkdir(parents=True)
        
        backup_file = self.backup_dir / file_path.name
        shutil.copy2(file_path, backup_file)
        
    def fix_readme_main(self):
        """Corrige el README.md principal."""
        readme_path = self.project_root / "README.md"
        if not readme_path.exists():
            return
            
        print("🔧 Corrigiendo README.md principal...")
        self.backup_file(readme_path)
        
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Eliminar referencias a scripts que no existen
        content = re.sub(
            r'```bash\s*# Show predefined test cases\s*python demo_extractor_mejorado\.py --test-cases.*?```',
            '```bash\n# Usar el launcher unificado\npython main.py --help\n```',
            content,
            flags=re.DOTALL
        )
        
        # Actualizar ejemplos de batch processing
        content = re.sub(
            r'python demo_extractor_mejorado\.py',
            'python main.py --batch',
            content
        )
        
        # Actualizar comando de ejecución
        content = re.sub(
            r'```bash\s*python run_gui\.py\s*```',
            '```bash\npython main.py\n```',
            content
        )
        
        # Eliminar referencias a archivos que no existen
        files_to_remove = [
            'demo_extractor_mejorado.py',
            'compare_extraction_methods.py',
            'improved_file_handler.py'
        ]
        
        for file_ref in files_to_remove:
            content = re.sub(f'[^\n]*{re.escape(file_ref)}[^\n]*\n?', '', content)
        
        if content != original_content:
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.fixes_applied.append("README.md principal actualizado")
    
    def fix_gui_readme(self):
        """Corrige el README.md de src/gui."""
        gui_readme_path = self.project_root / "src" / "gui" / "README.md"
        if not gui_readme_path.exists():
            return
            
        print("🔧 Corrigiendo src/gui/README.md...")
        self.backup_file(gui_readme_path)
        
        with open(gui_readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Actualizar estructura real
        old_structure = """src/gui/
├── models/              # Modelos y lógica de negocio
│   ├── genre_model.py  # Procesamiento de géneros
│   └── mpc_server.py   # Interfaz con servidor MPC
│
├── widgets/            # Widgets personalizados
│   ├── file_list_widget.py
│   ├── control_panel.py
│   ├── backup_panel.py
│   └── results_panel.py
│
├── threads/           # Procesamiento asíncrono
│   └── processing_thread.py
│
├── main_window.py    # Ventana principal
└── style.py         # Estilos y temas"""

        new_structure = """src/gui/
├── models/                      # Modelos y lógica de negocio
│   └── genre_model.py          # Procesamiento de géneros
│
├── widgets/                     # Widgets personalizados
│   ├── file_list_widget.py
│   ├── control_panel.py
│   ├── backup_panel.py
│   ├── file_results_table_widget.py
│   └── results_panel.py
│
├── threads/                     # Procesamiento asíncrono
│   ├── processing_thread.py
│   └── task_queue.py
│
├── i18n/                        # Internacionalización
│   └── translations/
│       ├── en.json
│       └── es.json
│
├── main_window.py              # Ventana principal
└── style.py                   # Estilos y temas"""
        
        content = content.replace(old_structure, new_structure)
        
        # Eliminar referencias a archivos que no existen
        content = re.sub(r'[^\n]*mpc_server\.py[^\n]*\n?', '', content)
        
        # Actualizar sección de componentes
        components_old = """### Modelos
- `GenreModel`: Procesamiento de géneros
- `MPCServer`: Comunicación con servidor MPC"""
        
        components_new = """### Modelos
- `GenreModel`: Procesamiento de géneros y metadatos"""
        
        content = content.replace(components_old, components_new)
        
        if content != original_content:
            with open(gui_readme_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.fixes_applied.append("src/gui/README.md actualizado")
    
    def fix_maintenance_guide(self):
        """Corrige MAINTENANCE_GUIDE.md."""
        guide_path = self.project_root / "MAINTENANCE_GUIDE.md"
        if not guide_path.exists():
            return
            
        print("🔧 Corrigiendo MAINTENANCE_GUIDE.md...")
        self.backup_file(guide_path)
        
        with open(guide_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Corregir comandos que no funcionan
        content = re.sub(
            r'python monitor_system_health\.py',
            'python3 monitor_system_health.py',
            content
        )
        
        # Agregar nota sobre scripts disponibles
        if "# COMANDOS DE VERIFICACIÓN RÁPIDA" in content:
            note = "\n> **Nota**: Verifica que los scripts mencionados existan antes de ejecutar los comandos.\n"
            content = content.replace(
                "# COMANDOS DE VERIFICACIÓN RÁPIDA",
                "# COMANDOS DE VERIFICACIÓN RÁPIDA" + note
            )
        
        if content != original_content:
            with open(guide_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.fixes_applied.append("MAINTENANCE_GUIDE.md actualizado")
    
    def fix_cleanup_reports(self):
        """Corrige reportes de cleanup que mencionan archivos eliminados."""
        cleanup_files = [
            "cleanup_analysis.md",
            "cleanup_final_report.md"
        ]
        
        for filename in cleanup_files:
            file_path = self.project_root / filename
            if not file_path.exists():
                continue
                
            print(f"🔧 Corrigiendo {filename}...")
            self.backup_file(file_path)
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Agregar nota de obsolescencia al inicio
            if not content.startswith("# ⚠️ DOCUMENTO HISTÓRICO"):
                header = """# ⚠️ DOCUMENTO HISTÓRICO
> **Nota**: Este documento refleja el estado del proyecto en el momento de la limpieza.
> Algunos archivos mencionados pueden haber sido eliminados o movidos.
> Para el estado actual, consultar la documentación principal.

---

"""
                content = header + content
            
            # Marcar referencias a archivos eliminados
            files_removed = [
                'demo_extractor_mejorado.py',
                'mp3_tool.py',
                'analyze_directory.py',
                'src/run_gui.py'
            ]
            
            for removed_file in files_removed:
                content = re.sub(
                    f'(`{re.escape(removed_file)}`)',
                    f'~~`{removed_file}`~~ *(eliminado)*',
                    content
                )
            
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.fixes_applied.append(f"{filename} actualizado")
    
    def create_structure_documentation(self):
        """Crea documentación actualizada de la estructura."""
        structure_doc = self.project_root / "ESTRUCTURA_ACTUAL.md"
        
        print("📄 Creando documentación de estructura actual...")
        
        content = """# 📁 ESTRUCTURA ACTUAL DEL PROYECTO
**Generado automáticamente el:** {date}

## 🏗️ Estructura Real

```
proyecto/
├── main.py                     # 🚀 Punto de entrada principal
├── app.py                      # 🔗 Alias de compatibilidad
├── src/
│   ├── __main__.py            # 🎯 CLI moderno
│   ├── core/                  # 🧠 Lógica de negocio
│   │   ├── enhanced_mp3_handler.py
│   │   ├── file_handler.py
│   │   ├── genre_detector.py
│   │   ├── genre_normalizer.py
│   │   ├── music_apis.py
│   │   ├── spotify_api.py
│   │   ├── data_validator.py
│   │   ├── error_handler.py
│   │   └── performance_monitor.py
│   └── gui/                   # 🖥️ Interfaz gráfica
│       ├── main_window.py
│       ├── style.py
│       ├── models/
│       │   └── genre_model.py
│       ├── widgets/
│       │   ├── control_panel.py
│       │   ├── backup_panel.py
│       │   ├── file_list_widget.py
│       │   ├── file_results_table_widget.py
│       │   └── results_panel.py
│       ├── threads/
│       │   ├── processing_thread.py
│       │   └── task_queue.py
│       └── i18n/
│           └── translations/
├── config/                    # ⚙️ Configuración
│   ├── api_keys.json
│   ├── dynamic_settings.json
│   └── genre_fallbacks.json
├── tests/                     # 🧪 Pruebas
└── docs/                      # 📚 Documentación
```

## 🚀 Comandos Principales

```bash
# Launcher unificado (recomendado)
python main.py

# Modos específicos
python main.py --gui          # Interfaz gráfica
python main.py --cli          # Línea de comandos
python main.py --batch        # Procesamiento masivo

# Scripts especializados (legacy)
python simple_batch_processor.py
python batch_process_mp3.py
```

## 📋 Archivos de Configuración

| Archivo | Propósito |
|---------|-----------|
| `config/api_keys.json` | Credenciales de APIs |
| `config/dynamic_settings.json` | Configuración dinámica |
| `config/genre_fallbacks.json` | Géneros de respaldo |

## 🔧 Scripts de Mantenimiento

| Script | Función |
|--------|---------|
| `validate_documentation.py` | Validar consistencia docs |
| `fix_documentation.py` | Corregir problemas docs |
| `monitor_system_health.py` | Monitoreo del sistema |

---

> 📝 **Nota**: Esta estructura es la real y actualizada. 
> Cualquier discrepancia con otros documentos debe reportarse.
""".format(date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        with open(structure_doc, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.fixes_applied.append("ESTRUCTURA_ACTUAL.md creado")
    
    def generate_report(self):
        """Genera reporte de correcciones aplicadas."""
        print("\n" + "="*60)
        print("📋 REPORTE DE CORRECCIONES APLICADAS")
        print("="*60)
        
        if not self.fixes_applied:
            print("ℹ️ No se aplicaron correcciones automáticas.")
            return
        
        print(f"✅ Se aplicaron {len(self.fixes_applied)} correcciones:")
        for fix in self.fixes_applied:
            print(f"   • {fix}")
        
        print(f"\n💾 Respaldos creados en: {self.backup_dir}")
        print("\n📝 Próximos pasos manuales:")
        print("   1. Revisar los archivos modificados")
        print("   2. Verificar que los comandos funcionen")
        print("   3. Ejecutar: python3 validate_documentation.py")
        print("   4. Corregir problemas restantes manualmente")
    
    def run_fixes(self, auto_fix=False):
        """Ejecuta todas las correcciones."""
        print("🔧 Iniciando correcciones automáticas de documentación...")
        
        if not auto_fix:
            response = input("¿Continuar con las correcciones? (y/N): ")
            if response.lower() != 'y':
                print("❌ Correcciones canceladas.")
                return False
        
        self.fix_readme_main()
        self.fix_gui_readme()
        self.fix_maintenance_guide()
        self.fix_cleanup_reports()
        self.create_structure_documentation()
        
        self.generate_report()
        return True

def main():
    parser = argparse.ArgumentParser(description="Corrige problemas de consistencia en documentación")
    parser.add_argument("--project-root", default=".", help="Ruta raíz del proyecto")
    parser.add_argument("--auto-fix", action="store_true", help="Aplicar correcciones sin confirmar")
    parser.add_argument("--backup-only", action="store_true", help="Solo crear respaldos")
    
    args = parser.parse_args()
    
    fixer = DocumentationFixer(args.project_root)
    
    if args.backup_only:
        # Solo crear respaldos de archivos críticos
        critical_files = ["README.md", "src/gui/README.md", "MAINTENANCE_GUIDE.md"]
        for filename in critical_files:
            file_path = Path(args.project_root) / filename
            if file_path.exists():
                fixer.backup_file(file_path)
        print(f"💾 Respaldos creados en: {fixer.backup_dir}")
        return
    
    success = fixer.run_fixes(args.auto_fix)
    
    if success:
        print("\n🎉 Correcciones completadas exitosamente")
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    main() 