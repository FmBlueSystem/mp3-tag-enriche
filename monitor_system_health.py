#!/usr/bin/env python3
"""
Script de monitoreo de salud del sistema de detección de géneros musicales.
Ejecuta verificaciones automáticas y genera reportes de estado.

Uso:
    python monitor_system_health.py [--full] [--output=report.json]
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemHealthMonitor:
    """Monitor de salud del sistema."""
    
    def __init__(self):
        self.checks = []
        self.results = {}
        self.start_time = datetime.now()
        
    def add_check(self, name: str, check_func, critical: bool = False):
        """Añade una verificación al monitor."""
        self.checks.append({
            'name': name,
            'function': check_func,
            'critical': critical
        })
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Ejecuta todas las verificaciones."""
        logger.info("🏥 Iniciando verificación de salud del sistema")
        
        passed = 0
        failed = 0
        warnings = 0
        critical_failures = 0
        
        for check in self.checks:
            try:
                logger.info(f"🔍 Ejecutando: {check['name']}")
                start = time.time()
                
                result = check['function']()
                duration = time.time() - start
                
                self.results[check['name']] = {
                    'status': 'PASS' if result['success'] else 'FAIL',
                    'success': result['success'],
                    'message': result.get('message', ''),
                    'details': result.get('details', {}),
                    'duration': round(duration, 3),
                    'critical': check['critical'],
                    'timestamp': datetime.now().isoformat()
                }
                
                if result['success']:
                    passed += 1
                    logger.info(f"✅ {check['name']} - OK ({duration:.3f}s)")
                else:
                    failed += 1
                    if check['critical']:
                        critical_failures += 1
                    level = "CRÍTICO" if check['critical'] else "FALLO"
                    logger.error(f"❌ {check['name']} - {level}: {result.get('message', '')}")
                    
            except Exception as e:
                failed += 1
                if check['critical']:
                    critical_failures += 1
                self.results[check['name']] = {
                    'status': 'ERROR',
                    'success': False,
                    'message': str(e),
                    'details': {'exception': type(e).__name__},
                    'duration': 0,
                    'critical': check['critical'],
                    'timestamp': datetime.now().isoformat()
                }
                logger.error(f"💥 {check['name']} - ERROR: {e}")
        
        # Generar resumen
        total_checks = len(self.checks)
        success_rate = (passed / total_checks) * 100 if total_checks > 0 else 0
        
        summary = {
            'total_checks': total_checks,
            'passed': passed,
            'failed': failed,
            'warnings': warnings,
            'critical_failures': critical_failures,
            'success_rate': round(success_rate, 1),
            'overall_status': self._determine_overall_status(critical_failures, success_rate),
            'execution_time': round((datetime.now() - self.start_time).total_seconds(), 3),
            'timestamp': datetime.now().isoformat()
        }
        
        return {
            'summary': summary,
            'checks': self.results,
            'metadata': {
                'script_version': '1.0',
                'python_version': sys.version,
                'working_directory': str(Path.cwd())
            }
        }
    
    def _determine_overall_status(self, critical_failures: int, success_rate: float) -> str:
        """Determina el estado general del sistema."""
        if critical_failures > 0:
            return "CRITICAL"
        elif success_rate >= 95:
            return "HEALTHY"
        elif success_rate >= 80:
            return "WARNING"
        else:
            return "UNHEALTHY"

def check_improvements_implemented() -> Dict[str, Any]:
    """Verifica que las mejoras estén implementadas."""
    try:
        # Verificar archivos críticos
        required_files = [
            'src/core/error_handler.py',
            'src/core/performance_monitor.py',
            'src/core/data_validator.py',
            'config/dynamic_settings.json'
        ]
        
        missing_files = []
        for file_path in required_files:
            if not Path(file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            return {
                'success': False,
                'message': f"Archivos críticos faltantes: {missing_files}",
                'details': {'missing_files': missing_files}
            }
        
        return {
            'success': True,
            'message': "Todas las mejoras están implementadas",
            'details': {'verified_files': len(required_files)}
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Error verificando mejoras: {e}",
            'details': {'exception': str(e)}
        }

def check_configuration_files() -> Dict[str, Any]:
    """Verifica archivos de configuración."""
    try:
        config_files = [
            'config/dynamic_settings.json',
            'config/genre_fallbacks.json',
            'comprehensive_improvement_summary.json'
        ]
        
        valid_configs = 0
        invalid_configs = []
        
        for config_file in config_files:
            try:
                if Path(config_file).exists():
                    with open(config_file, 'r') as f:
                        json.load(f)  # Verificar que es JSON válido
                    valid_configs += 1
                else:
                    invalid_configs.append(f"{config_file} (no existe)")
            except json.JSONDecodeError:
                invalid_configs.append(f"{config_file} (JSON inválido)")
        
        if invalid_configs:
            return {
                'success': False,
                'message': f"Configuraciones inválidas: {invalid_configs}",
                'details': {'invalid_configs': invalid_configs, 'valid_configs': valid_configs}
            }
        
        return {
            'success': True,
            'message': f"Todas las configuraciones son válidas ({valid_configs})",
            'details': {'valid_configs': valid_configs}
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Error verificando configuraciones: {e}",
            'details': {'exception': str(e)}
        }

def check_core_modules_importable() -> Dict[str, Any]:
    """Verifica que los módulos core se puedan importar."""
    try:
        modules_to_test = [
            'src.core.error_handler',
            'src.core.performance_monitor', 
            'src.core.data_validator',
            'src.core.genre_normalizer',
            'src.core.config_loader'
        ]
        
        import_results = {}
        failed_imports = []
        
        for module in modules_to_test:
            try:
                __import__(module)
                import_results[module] = True
            except ImportError as e:
                import_results[module] = False
                failed_imports.append(f"{module}: {e}")
        
        if failed_imports:
            return {
                'success': False,
                'message': f"Fallos de importación: {failed_imports}",
                'details': {'import_results': import_results, 'failed_imports': failed_imports}
            }
        
        return {
            'success': True,
            'message': f"Todos los módulos se importan correctamente ({len(modules_to_test)})",
            'details': {'import_results': import_results}
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Error verificando importaciones: {e}",
            'details': {'exception': str(e)}
        }

def check_test_suite_status() -> Dict[str, Any]:
    """Verifica el estado de la suite de tests."""
    try:
        import subprocess
        
        # Ejecutar test_improvements.py
        result = subprocess.run(
            [sys.executable, 'test_improvements.py'],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            # Parsear output para obtener estadísticas
            output_lines = result.stdout.split('\n')
            success_rate = None
            total_tests = None
            
            for line in output_lines:
                if 'Tasa de éxito:' in line:
                    try:
                        success_rate = float(line.split(':')[1].strip().replace('%', ''))
                    except:
                        pass
                elif 'Total de pruebas:' in line:
                    try:
                        total_tests = int(line.split(':')[1].strip())
                    except:
                        pass
            
            return {
                'success': True,
                'message': f"Tests de mejoras: {success_rate}% éxito",
                'details': {
                    'success_rate': success_rate,
                    'total_tests': total_tests,
                    'stdout': result.stdout[-500:] if result.stdout else ''  # Últimas 500 chars
                }
            }
        else:
            return {
                'success': False,
                'message': f"Tests fallaron con código {result.returncode}",
                'details': {
                    'returncode': result.returncode,
                    'stderr': result.stderr[-500:] if result.stderr else '',
                    'stdout': result.stdout[-500:] if result.stdout else ''
                }
            }
            
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'message': "Tests expiraron (timeout > 120s)",
            'details': {'timeout': 120}
        }
    except Exception as e:
        return {
            'success': False,
            'message': f"Error ejecutando tests: {e}",
            'details': {'exception': str(e)}
        }

def check_disk_space() -> Dict[str, Any]:
    """Verifica espacio en disco."""
    try:
        import shutil
        
        current_dir = Path.cwd()
        total, used, free = shutil.disk_usage(current_dir)
        
        # Convertir a GB
        total_gb = total / (1024**3)
        used_gb = used / (1024**3)
        free_gb = free / (1024**3)
        usage_percent = (used / total) * 100
        
        # Verificar si hay suficiente espacio libre (mínimo 1GB)
        if free_gb < 1:
            return {
                'success': False,
                'message': f"Espacio en disco bajo: {free_gb:.1f}GB libres",
                'details': {
                    'total_gb': round(total_gb, 1),
                    'used_gb': round(used_gb, 1),
                    'free_gb': round(free_gb, 1),
                    'usage_percent': round(usage_percent, 1)
                }
            }
        
        return {
            'success': True,
            'message': f"Espacio suficiente: {free_gb:.1f}GB libres ({usage_percent:.1f}% usado)",
            'details': {
                'total_gb': round(total_gb, 1),
                'used_gb': round(used_gb, 1),
                'free_gb': round(free_gb, 1),
                'usage_percent': round(usage_percent, 1)
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Error verificando espacio en disco: {e}",
            'details': {'exception': str(e)}
        }

def check_dependencies() -> Dict[str, Any]:
    """Verifica dependencias críticas."""
    try:
        critical_packages = [
            'mutagen', 'requests', 'PySide6', 'psutil', 'pathvalidate'
        ]
        
        missing_packages = []
        installed_packages = {}
        
        for package in critical_packages:
            try:
                module = __import__(package)
                version = getattr(module, '__version__', 'unknown')
                installed_packages[package] = version
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            return {
                'success': False,
                'message': f"Dependencias faltantes: {missing_packages}",
                'details': {
                    'missing_packages': missing_packages,
                    'installed_packages': installed_packages
                }
            }
        
        return {
            'success': True,
            'message': f"Todas las dependencias críticas están instaladas ({len(critical_packages)})",
            'details': {'installed_packages': installed_packages}
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"Error verificando dependencias: {e}",
            'details': {'exception': str(e)}
        }

def print_summary(results: Dict[str, Any]):
    """Imprime resumen del estado del sistema."""
    summary = results['summary']
    
    print("\n" + "="*60)
    print("🏥 REPORTE DE SALUD DEL SISTEMA")
    print("="*60)
    
    # Estado general
    status_icon = {
        'HEALTHY': '🟢',
        'WARNING': '🟡',
        'UNHEALTHY': '🟠',
        'CRITICAL': '🔴'
    }.get(summary['overall_status'], '⚪')
    
    print(f"Estado General: {status_icon} {summary['overall_status']}")
    print(f"Tasa de Éxito: {summary['success_rate']}%")
    print(f"Tiempo de Ejecución: {summary['execution_time']}s")
    print(f"Timestamp: {summary['timestamp']}")
    print()
    
    # Estadísticas
    print("📊 ESTADÍSTICAS:")
    print(f"  Total de Verificaciones: {summary['total_checks']}")
    print(f"  ✅ Pasaron: {summary['passed']}")
    print(f"  ❌ Fallaron: {summary['failed']}")
    print(f"  🔥 Fallos Críticos: {summary['critical_failures']}")
    print()
    
    # Detalles de verificaciones
    if summary['failed'] > 0:
        print("❌ VERIFICACIONES FALLIDAS:")
        for name, check in results['checks'].items():
            if not check['success']:
                icon = "🔥" if check['critical'] else "❌"
                print(f"  {icon} {name}: {check['message']}")
        print()
    
    # Recomendaciones
    print("💡 RECOMENDACIONES:")
    if summary['critical_failures'] > 0:
        print("  🚨 ACCIÓN INMEDIATA REQUERIDA: Revisar fallos críticos")
    elif summary['success_rate'] < 95:
        print("  ⚠️  Revisar verificaciones fallidas para mejorar estabilidad")
    else:
        print("  ✅ Sistema en estado óptimo - mantener monitoreo rutinario")
    
    print("\n" + "="*60)

def main():
    """Función principal."""
    parser = argparse.ArgumentParser(description='Monitor de salud del sistema de géneros musicales')
    parser.add_argument('--full', action='store_true', help='Ejecutar verificaciones completas (incluye tests)')
    parser.add_argument('--output', help='Archivo JSON para guardar resultados')
    parser.add_argument('--quiet', action='store_true', help='Solo mostrar errores')
    
    args = parser.parse_args()
    
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    
    # Crear monitor
    monitor = SystemHealthMonitor()
    
    # Agregar verificaciones básicas
    monitor.add_check("Mejoras Implementadas", check_improvements_implemented, critical=True)
    monitor.add_check("Archivos de Configuración", check_configuration_files, critical=True)
    monitor.add_check("Módulos Core Importables", check_core_modules_importable, critical=True)
    monitor.add_check("Dependencias Críticas", check_dependencies, critical=True)
    monitor.add_check("Espacio en Disco", check_disk_space)
    
    # Agregar verificaciones completas si se solicita
    if args.full:
        monitor.add_check("Suite de Tests", check_test_suite_status)
    
    # Ejecutar verificaciones
    results = monitor.run_all_checks()
    
    # Mostrar resumen
    if not args.quiet:
        print_summary(results)
    
    # Guardar resultados si se especifica
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 Resultados guardados en: {args.output}")
    
    # Código de salida basado en estado
    exit_code = {
        'HEALTHY': 0,
        'WARNING': 1,
        'UNHEALTHY': 2,
        'CRITICAL': 3
    }.get(results['summary']['overall_status'], 4)
    
    sys.exit(exit_code)

if __name__ == '__main__':
    main() 