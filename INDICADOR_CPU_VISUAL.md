# Indicador Visual de CPU

## Descripción

El **Indicador Visual de CPU** es el complemento perfecto al indicador de memoria, proporcionando monitoreo en tiempo real del uso del procesador mediante un sistema visual claro y no intrusivo.

## Características Principales

### 🎨 **Indicación Visual por Colores**
- **🟢 Verde (Normal)**: CPU relajado (< 30%)
- **🟡 Amarillo (Moderado)**: Uso normal (30-60%)
- **🟠 Naranja (Alto)**: CPU trabajando duro (60-85%)
- **🔴 Rojo (Crítico)**: CPU saturado (> 85%)

### 📊 **Información en Tiempo Real**
- **Barra de Progreso**: Muestra el porcentaje de uso total de CPU
- **Cores Activos**: Indica cuántos cores están trabajando (>5% uso)
- **Estado Textual**: Descripción clara del nivel actual de CPU
- **Actualización Automática**: Se actualiza cada 2 segundos (normal) o cada segundo (durante procesamiento)

### 🔧 **Monitoreo Inteligente**
- **Detección por core**: Identifica cores individuales activos
- **Medición precisa**: Usa intervalos de 0.1s para mayor precisión
- **Estados dinámicos**: Cambia automáticamente según la carga

## Ubicación en la Interfaz

El indicador se encuentra en la **barra superior** de la aplicación, junto al indicador de memoria:

```
[Idioma] [Memoria: ██████ 45.2% ● Normal] [CPU: ████ 23.5% ● Normal Cores: 2/8] [Tema]
```

## Estados de CPU

### 🟢 Normal (< 30% CPU)
- **Color**: Verde brillante
- **Comportamiento**: CPU relajado, recursos abundantes
- **Significado**: Sistema funcionando óptimamente
- **Acciones**: Ninguna acción requerida

### 🟡 Moderado (30-60% CPU)
- **Color**: Amarillo
- **Comportamiento**: Uso normal de CPU
- **Significado**: Sistema trabajando normalmente
- **Acciones**: Monitoreo continuo

### 🟠 Alto (60-85% CPU)
- **Color**: Naranja
- **Comportamiento**: CPU trabajando intensivamente
- **Significado**: Sistema bajo carga considerable
- **Acciones**: Vigilancia aumentada, posible optimización

### 🔴 Crítico (> 85% CPU)
- **Color**: Rojo
- **Comportamiento**: CPU saturado
- **Significado**: Riesgo de degradación del rendimiento
- **Acciones**: 
  - Alertas automáticas en logs
  - Monitoreo más frecuente
  - Posible reducción de cargas

## Información Técnica

### **Métricas Monitoreadas**
- **CPU Total**: Porcentaje de uso promedio
- **CPU por Core**: Uso individual de cada core
- **Cores Activos**: Cores con >5% de utilización
- **Core Máximo**: El core con mayor utilización

### **Algoritmo de Detección**
```python
def _determine_pressure_level(self, cpu_percent: float) -> str:
    if cpu_percent >= 85:
        return "CRÍTICO"
    elif cpu_percent >= 60:
        return "ALTO"
    elif cpu_percent >= 30:
        return "MODERADO"
    else:
        return "NORMAL"
```

### **Actualización Inteligente**
- **Intervalo normal**: 2 segundos
- **Intervalo procesamiento**: 1 segundo
- **Medición precisa**: 0.1s para obtener datos exactos

## Integración con el Sistema

### **Durante el Procesamiento**
- **Frecuencia aumentada**: Actualización cada segundo
- **Monitoreo activo**: Vigilancia continua del CPU
- **Alertas automáticas**: Registro de estados críticos
- **Coordinación**: Trabaja junto con el indicador de memoria

### **En Estado Normal**
- **Frecuencia estándar**: Actualización cada 2 segundos
- **Monitoreo pasivo**: Seguimiento regular del sistema
- **Estado informativo**: Muestra información actual

## Señales y Eventos

El indicador emite señales que se manejan discretamente:

```python
# Señales emitidas
cpu_critical = Signal()  # CPU crítica detectada
cpu_high = Signal()      # CPU alta detectada  
cpu_normal = Signal()    # CPU normal

# Manejadores en MainWindow
def on_cpu_critical(self):
    logger.critical("Estado crítico de CPU detectado")
    self.statusBar().showMessage("⚠️ CPU crítica", 3000)

def on_cpu_high(self):
    logger.warning("Estado alto de CPU detectado")
    self.statusBar().showMessage("⚠️ CPU alta", 2000)
    
def on_cpu_normal(self):
    logger.info("CPU ha vuelto a niveles normales")
    self.statusBar().showMessage("✅ CPU normal", 1000)
```

## Casos de Uso

### **Para Usuarios**
- **Monitoreo visual**: Ver estado del CPU sin interrupciones
- **Detección temprana**: Identificar cuándo el CPU está saturado
- **Optimización**: Saber cuándo el sistema puede manejar más carga
- **Troubleshooting**: Diagnosticar problemas de rendimiento

### **Durante Procesamiento de Archivos**
- **Carga balanceada**: Ver si el CPU está siendo subutilizado
- **Detección de cuellos de botella**: Identificar si CPU es el limitante
- **Optimización de lotes**: Ajustar tamaños según capacidad de CPU
- **Monitoreo de rendimiento**: Evaluar eficiencia del procesamiento

## Beneficios de UX

### ✅ **Información Continua**
- Siempre visible en la barra superior
- No requiere abrir ventanas adicionales
- Actualización automática en tiempo real

### ✅ **Sin Interrupciones**
- No aparecen diálogos emergentes
- Alertas discretas en barra de estado
- Flujo de trabajo continuo

### ✅ **Visualmente Intuitivo**
- Colores universalmente reconocidos
- Barra de progreso clara
- Información textual descriptiva

## Archivos Técnicos

### **Nuevo Archivo Principal**
- `src/gui/widgets/cpu_indicator.py` - Widget del indicador (240+ líneas)

### **Archivos Modificados**
- `src/gui/main_window.py` - Integración en la interfaz
- `src/gui/widgets/__init__.py` - Exportación del widget

### **Scripts de Prueba**
- `test_cpu_indicator.py` - Prueba individual del CPU
- `test_system_indicators.py` - Prueba conjunta memoria + CPU

## Pruebas Incluidas

### **Test Individual de CPU**
```bash
python3 test_cpu_indicator.py
```

**Funcionalidades:**
- ✅ Monitoreo en tiempo real
- ✅ Simulación de cargas (ligera/moderada/pesada)
- ✅ Información detallada por core
- ✅ Control de intensidad de carga

### **Test de Sistema Completo**
```bash
python3 test_system_indicators.py
```

**Funcionalidades:**
- ✅ Indicadores memoria + CPU juntos
- ✅ Modo procesamiento
- ✅ Simulaciones coordinadas
- ✅ Interface profesional

## Configuración y Personalización

### **Umbrales Ajustables**
Los umbrales pueden modificarse en el código:
```python
# En cpu_indicator.py
NORMAL = 30      # < 30%
MODERADO = 60    # 30-60%
ALTO = 85        # 60-85%
CRÍTICO = 85     # > 85%
```

### **Colores Personalizables**
Los colores se pueden cambiar en los métodos `_set_*_style()`:
```python
VERDE = "#44AA44"    # Normal
AMARILLO = "#FFAA00" # Moderado  
NARANJA = "#FF8800"  # Alto
ROJO = "#FF4444"     # Crítico
```

## Rendimiento y Optimización

### **Impacto del Sistema**
- **CPU adicional**: < 0.2% (mínimo)
- **Memoria adicional**: ~3MB para el widget
- **Precisión**: Intervalos de 0.1s para medición exacta
- **Eficiencia**: Actualización solo cuando hay cambios

### **Optimizaciones Incluidas**
- Medición eficiente con `psutil`
- Timers ajustables según contexto
- Detección inteligente de cores activos
- Logging condicional para debugging

## Compatibilidad

- **Sistema Operativo**: macOS, Windows, Linux
- **Python**: 3.8+
- **PySide6**: Totalmente compatible
- **Temas**: Se adapta automáticamente
- **Accesibilidad**: Mantiene soporte completo

## Conclusión

El **Indicador Visual de CPU** completa el sistema de monitoreo de recursos, proporcionando:

- **Información valiosa** sobre el estado del procesador
- **Integración perfecta** con el indicador de memoria
- **Experiencia no intrusiva** que mejora la productividad
- **Herramienta de diagnóstico** para optimización de rendimiento

Junto con el indicador de memoria, forma un sistema completo de monitoreo visual que transforma la experiencia de usuario de manera profesional y elegante. 