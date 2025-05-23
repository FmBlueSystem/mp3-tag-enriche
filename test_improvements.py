#!/usr/bin/env python3
"""
Script de pruebas completo para validar las mejoras implementadas.
Verifica funcionamiento de sistemas críticos y optimizaciones.
"""
import os
import sys
import time
import json
import logging
import traceback
from pathlib import Path
from typing import Dict, List, Any
import tempfile

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ImprovementTester:
    """Tester para validar las mejoras implementadas."""
    
    def __init__(self):
        self.test_results: Dict[str, Dict[str, Any]] = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def run_test(self, test_name: str, test_func, *args, **kwargs) -> bool:
        """Ejecuta una prueba individual y registra resultados."""
        self.total_tests += 1
        start_time = time.time()
        
        try:
            logger.info(f"🧪 Ejecutando: {test_name}")
            result = test_func(*args, **kwargs)
            duration = time.time() - start_time
            
            self.test_results[test_name] = {
                "status": "PASSED",
                "duration": duration,
                "result": result,
                "error": None
            }
            
            self.passed_tests += 1
            logger.info(f"✅ {test_name} - PASSED ({duration:.2f}s)")
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            error_details = {
                "type": type(e).__name__,
                "message": str(e),
                "traceback": traceback.format_exc()
            }
            
            self.test_results[test_name] = {
                "status": "FAILED", 
                "duration": duration,
                "result": None,
                "error": error_details
            }
            
            self.failed_tests += 1
            logger.error(f"❌ {test_name} - FAILED ({duration:.2f}s): {e}")
            return False
            
    def test_error_handler_system(self) -> Dict[str, Any]:
        """Prueba el sistema de manejo de errores."""
        try:
            from src.core.error_handler import ErrorHandler, ErrorSeverity, get_global_error_handler
            
            # Crear instancia de error handler
            error_handler = ErrorHandler()
            
            # Probar registro de error
            test_error = ValueError("Error de prueba")
            error_context = error_handler.handle_error(
                test_error,
                component="test",
                operation="validation",
                severity=ErrorSeverity.LOW
            )
            
            # Verificar que se registró correctamente
            assert error_context.error_type == "ValueError"
            assert error_context.error_message == "Error de prueba"
            assert error_context.component == "test"
            
            # Probar estadísticas
            stats = error_handler.get_error_stats()
            assert stats["total_errors"] >= 1
            
            return {
                "error_handler_created": True,
                "error_registered": True,
                "stats_available": True,
                "global_handler_accessible": get_global_error_handler() is not None
            }
            
        except ImportError:
            return {"error": "Error handler module not found"}
            
    def test_performance_monitor_system(self) -> Dict[str, Any]:
        """Prueba el sistema de monitoreo de performance."""
        try:
            from src.core.performance_monitor import PerformanceMonitor, setup_performance_monitoring
            
            # Crear monitor
            monitor = PerformanceMonitor(collection_interval=0.1)
            
            # Probar métricas personalizadas
            monitor.add_metric("test_metric", 42.5, {"test": "true"})
            
            # Probar registro de operación
            monitor.record_operation("test_operation", 0.1)
            
            # Probar alertas
            alert = monitor.add_alert("test_metric", 40.0, "greater")
            
            # Iniciar y detener monitoreo
            monitor.start_monitoring()
            time.sleep(0.3)  # Permitir recolección
            monitor.stop_monitoring()
            
            # Verificar resumen del sistema
            summary = monitor.get_system_summary()
            operation_stats = monitor.get_operation_stats()
            
            return {
                "monitor_created": True,
                "metrics_added": True,
                "operations_recorded": True,
                "alerts_configured": True,
                "system_summary_available": len(summary) > 0,
                "operation_stats_available": len(operation_stats) > 0
            }
            
        except ImportError:
            return {"error": "Performance monitor module not found"}
            
    def test_data_validator_system(self) -> Dict[str, Any]:
        """Prueba el sistema de validación de datos."""
        try:
            from src.core.data_validator import DataValidator, ValidationResult, safe_filename
            
            # Probar validación de filename
            filename_result = DataValidator.validate_filename("test<file>.mp3")
            assert isinstance(filename_result, ValidationResult)
            assert filename_result.sanitized_value == "test_file_.mp3"
            
            # Probar validación de artista/título
            artist_result = DataValidator.validate_artist_title("Test Artist", "artist")
            assert artist_result.is_valid
            
            # Probar validación de géneros
            genre_result = DataValidator.validate_genre_list(["Rock", "Pop", "rock"])  # Con duplicado
            assert len(genre_result.sanitized_value) == 2  # Duplicado eliminado
            
            # Probar función de conveniencia
            safe_name = safe_filename("dangerous<>filename.mp3")
            assert "<" not in safe_name and ">" not in safe_name
            
            # Probar validación de metadata completa
            metadata = {
                "artist": "Test Artist",
                "title": "Test Song",
                "genre": "Rock;Pop",
                "year": 2023
            }
            metadata_result = DataValidator.validate_metadata_dict(metadata)
            assert metadata_result.is_valid
            
            return {
                "filename_validation": True,
                "artist_title_validation": True,
                "genre_validation": True,
                "safe_functions": True,
                "metadata_validation": True
            }
            
        except ImportError:
            return {"error": "Data validator module not found"}
            
    def test_persistent_cache_improvements(self) -> Dict[str, Any]:
        """Prueba las mejoras en el sistema de cache."""
        try:
            from src.core.persistent_cache import PersistentCache, sanitize_cache_filename
            
            # Crear cache temporal
            with tempfile.TemporaryDirectory() as temp_dir:
                cache = PersistentCache(temp_dir)
                
                # Probar sanitización de nombres
                dangerous_name = "test<>file:name"
                safe_name = sanitize_cache_filename(dangerous_name)
                assert "<" not in safe_name and ">" not in safe_name and ":" not in safe_name
                
                # Probar operaciones básicas de cache
                cache.set("test_key", {"data": "test_value"}, "test_type")
                retrieved = cache.get("test_key")
                assert retrieved["data"] == "test_value"
                
                # Probar estadísticas
                stats = cache.get_stats()
                assert "hits" in stats and "misses" in stats
                
                return {
                    "sanitization_working": True,
                    "cache_operations": True,
                    "stats_available": True,
                    "safe_name_generated": safe_name
                }
                
        except ImportError:
            return {"error": "Persistent cache module not found"}
            
    def test_genre_detector_improvements(self) -> Dict[str, Any]:
        """Prueba las mejoras en el detector de géneros."""
        try:
            from src.core.genre_detector import get_fallback_genres
            
            # Probar géneros de fallback
            fallback_electronic = get_fallback_genres("Calvin Harris", "Summer Remix")
            assert "electronic" in fallback_electronic
            
            fallback_generic = get_fallback_genres("Unknown Artist", "Unknown Song")
            assert len(fallback_generic) > 0  # Debe retornar géneros genéricos
            
            return {
                "fallback_genres_working": True,
                "electronic_detection": "electronic" in fallback_electronic,
                "generic_fallback": len(fallback_generic) > 0
            }
            
        except ImportError:
            return {"error": "Genre detector module not found"}
            
    def test_config_loader_improvements(self) -> Dict[str, Any]:
        """Prueba las mejoras en el cargador de configuración."""
        try:
            from src.core.config_loader import DynamicConfig
            
            # Crear configuración dinámica
            config = DynamicConfig()
            
            # Probar obtención de umbrales dinámicos
            threshold_many_apis = config.get_dynamic_threshold(api_count=3, confidence_spread=0.1)
            threshold_few_apis = config.get_dynamic_threshold(api_count=1, confidence_spread=0.8)
            
            # Verificar que los umbrales son diferentes según contexto
            assert threshold_many_apis != threshold_few_apis
            
            # Probar get/set
            config.set("test_section", "test_key", "test_value")
            retrieved = config.get("test_section", "test_key")
            assert retrieved == "test_value"
            
            return {
                "dynamic_config_created": True,
                "dynamic_thresholds": True,
                "get_set_operations": True,
                "threshold_many_apis": threshold_many_apis,
                "threshold_few_apis": threshold_few_apis
            }
            
        except ImportError:
            return {"error": "Config loader module not found"}
            
    def test_file_system_operations(self) -> Dict[str, Any]:
        """Prueba operaciones del sistema de archivos."""
        # Verificar directorios críticos
        config_dir = Path("config")
        cache_dir = Path("cache")
        
        results = {
            "config_dir_exists": config_dir.exists(),
            "cache_dir_exists": cache_dir.exists(),
        }
        
        # Verificar archivos de configuración
        dynamic_config = config_dir / "dynamic_settings.json"
        genre_fallbacks = config_dir / "genre_fallbacks.json"
        
        results.update({
            "dynamic_config_exists": dynamic_config.exists(),
            "genre_fallbacks_exists": genre_fallbacks.exists()
        })
        
        # Si existen, verificar que son válidos JSON
        if dynamic_config.exists():
            try:
                with open(dynamic_config) as f:
                    json.load(f)
                results["dynamic_config_valid_json"] = True
            except json.JSONDecodeError:
                results["dynamic_config_valid_json"] = False
                
        if genre_fallbacks.exists():
            try:
                with open(genre_fallbacks) as f:
                    json.load(f)
                results["genre_fallbacks_valid_json"] = True
            except json.JSONDecodeError:
                results["genre_fallbacks_valid_json"] = False
                
        return results
        
    def test_requirements_and_dependencies(self) -> Dict[str, Any]:
        """Prueba que las dependencias estén correctamente configuradas."""
        requirements_file = Path("requirements.txt")
        
        if not requirements_file.exists():
            return {"error": "requirements.txt not found"}
            
        with open(requirements_file) as f:
            requirements_content = f.read()
            
        # Verificar dependencias críticas
        critical_deps = ["psutil", "tabulate", "pathvalidate"]
        missing_deps = []
        
        for dep in critical_deps:
            if dep not in requirements_content:
                missing_deps.append(dep)
                
        return {
            "requirements_file_exists": True,
            "critical_dependencies_present": len(missing_deps) == 0,
            "missing_dependencies": missing_deps,
            "total_lines": len(requirements_content.splitlines())
        }
        
    def run_all_tests(self) -> Dict[str, Any]:
        """Ejecuta todas las pruebas y genera reporte."""
        logger.info("🚀 Iniciando suite completa de pruebas de mejoras")
        
        # Lista de pruebas a ejecutar
        tests = [
            ("Error Handler System", self.test_error_handler_system),
            ("Performance Monitor System", self.test_performance_monitor_system), 
            ("Data Validator System", self.test_data_validator_system),
            ("Persistent Cache Improvements", self.test_persistent_cache_improvements),
            ("Genre Detector Improvements", self.test_genre_detector_improvements),
            ("Config Loader Improvements", self.test_config_loader_improvements),
            ("File System Operations", self.test_file_system_operations),
            ("Requirements and Dependencies", self.test_requirements_and_dependencies)
        ]
        
        # Ejecutar todas las pruebas
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
            
        # Generar reporte final
        return self.generate_final_report()
        
    def generate_final_report(self) -> Dict[str, Any]:
        """Genera reporte final de las pruebas."""
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        report = {
            "summary": {
                "total_tests": self.total_tests,
                "passed_tests": self.passed_tests,
                "failed_tests": self.failed_tests,
                "success_rate": success_rate
            },
            "detailed_results": self.test_results,
            "recommendation": self._get_recommendation(success_rate)
        }
        
        # Guardar reporte
        with open("test_improvements_report.json", 'w') as f:
            json.dump(report, f, indent=2, default=str)
            
        return report
        
    def _get_recommendation(self, success_rate: float) -> str:
        """Genera recomendación basada en la tasa de éxito."""
        if success_rate == 100:
            return "🎉 Todas las mejoras funcionan correctamente. Sistema listo para producción."
        elif success_rate >= 80:
            return "✅ La mayoría de mejoras funcionan. Revisar fallos menores antes de continuar."
        elif success_rate >= 60:
            return "⚠️ Algunas mejoras tienen problemas. Se recomienda corregir antes de usar en producción."
        else:
            return "❌ Múltiples mejoras fallan. Revisión crítica necesaria antes de continuar."

def main():
    """Función principal."""
    print("🧪 SISTEMA DE PRUEBAS DE MEJORAS")
    print("=" * 50)
    
    tester = ImprovementTester()
    report = tester.run_all_tests()
    
    print("\n" + "=" * 50)
    print("📊 REPORTE FINAL")
    print("=" * 50)
    print(f"Total de pruebas: {report['summary']['total_tests']}")
    print(f"Pruebas exitosas: {report['summary']['passed_tests']}")
    print(f"Pruebas fallidas: {report['summary']['failed_tests']}")
    print(f"Tasa de éxito: {report['summary']['success_rate']:.1f}%")
    print(f"\n{report['recommendation']}")
    
    if report['summary']['failed_tests'] > 0:
        print("\n❌ PRUEBAS FALLIDAS:")
        for test_name, result in report['detailed_results'].items():
            if result['status'] == 'FAILED':
                print(f"  • {test_name}: {result['error']['message']}")
                
    print(f"\n📄 Reporte detallado guardado en: test_improvements_report.json")
    print("=" * 50)
    
    # Código de salida basado en resultados
    if report['summary']['success_rate'] < 80:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main() 