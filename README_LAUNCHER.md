# 🎵 DETECTOR DE GÉNEROS MUSICALES - LAUNCHER UNIFICADO

## 🚀 NUEVO SISTEMA UNIFICADO

El proyecto ahora tiene un **punto de entrada único** que resuelve todos los conflictos entre interfaces CLI y GUI.

### ✅ **USO SIMPLIFICADO**

```bash
# Auto-detección inteligente
python main.py                          # Elige automáticamente GUI o CLI

# Modos específicos
python main.py --gui                     # Forzar interfaz gráfica
python main.py --cli                     # Forzar línea de comandos
python main.py --batch /directorio/     # Procesamiento masivo
python main.py --analyze archivo.mp3    # Solo análisis
```

## 🔧 **EJEMPLOS DE USO**

### **Modo Automático (Recomendado)**
```bash
python main.py
# Auto-detecta: GUI en macOS/Windows, CLI en servidores
```

### **Procesamiento CLI Directo**
```bash
python main.py --cli /ruta/archivo.mp3
python main.py --cli /directorio/ --recursive
python main.py --cli . --confidence 0.5 --max-genres 2
```

### **Análisis Sin Modificar**
```bash
python main.py --analyze archivo.mp3
python main.py --analyze /directorio/ --recursive
```

### **Procesamiento Batch Masivo**
```bash
python main.py --batch /directorio/ --workers 8
python main.py --batch /directorio/ --dry-run --debug
python main.py --batch /directorio/ --force --max-files 100
```

## 📊 **MIGRACIÓN DESDE VERSIONES ANTERIORES**

### **Antes (Múltiples Scripts):**
```bash
python run_gui.py                    # GUI
python enriquecer_mp3_cli.py         # CLI legacy
python -m src                        # CLI moderno
python batch_process_mp3.py          # Batch
```

### **Ahora (Un Solo Script):**
```bash
python main.py                       # Auto-detect
python main.py --gui                 # GUI
python main.py --cli                 # CLI unificado
python main.py --batch               # Batch integrado
```

## 🔍 **DETECCIÓN AUTOMÁTICA**

El launcher detecta automáticamente el mejor modo:

- **macOS/Windows**: GUI por defecto si está disponible
- **Linux con DISPLAY**: GUI si está disponible
- **Servidores/Sin GUI**: CLI automáticamente
- **Con argumentos específicos**: Modo especificado

## 📋 **OPCIONES DISPONIBLES**

### **Generales:**
- `--recursive, -r`: Procesar directorios recursivamente
- `--backup-dir`: Directorio para backups (default: configurado)
- `--confidence`: Umbral mínimo de confianza (0.0-1.0, default: 0.3)
- `--max-genres`: Máximo géneros a asignar (default: 3)
- `--no-spotify`: Deshabilitar API de Spotify
- `--verbose, -v`: Salida detallada

### **Específicas de Batch:**
- `--dry-run`: Solo simular cambios
- `--force`: Forzar actualización
- `--max-files`: Limitar archivos a procesar
- `--workers`: Procesos paralelos (default: 4)
- `--debug`: Información detallada

## 💡 **BENEFICIOS**

### **Para Usuarios:**
- ✅ **Un solo comando** para todo
- ✅ **Auto-detección inteligente** del mejor modo
- ✅ **Experiencia consistente** entre GUI y CLI
- ✅ **Menos confusión** sobre qué script usar

### **Para Desarrolladores:**
- ✅ **Código unificado** y menos duplicación
- ✅ **Configuración centralizada**
- ✅ **Testing simplificado**
- ✅ **Mantenimiento más fácil**

## 📦 **COMPATIBILIDAD**

### **Scripts Legacy (Aún Funcionan):**
Los scripts anteriores siguen funcionando para compatibilidad:
- `run_gui.py` → `python main.py --gui`
- `enriquecer_mp3_cli.py` → `python main.py --cli`
- `batch_process_mp3.py` → `python main.py --batch`

### **Alias de Compatibilidad:**
```bash
python app.py        # Alias para main.py
```

## 🔧 **CONFIGURACIÓN**

Todas las configuraciones se centralizan:
- APIs en `config/` 
- Paths en argumentos o auto-detección
- Logging unificado
- Backup directory consistente

## 🆕 **NUEVAS CARACTERÍSTICAS**

1. **Auto-detección de entorno**
2. **Fallbacks automáticos** (GUI → CLI si GUI no disponible)
3. **Configuración unificada** entre todos los modos
4. **Logging consistente** en todos los modos
5. **Mejor manejo de errores** con recuperación automática

## 🚀 **RECOMENDACIONES**

### **Nuevos Usuarios:**
```bash
python main.py  # ¡Eso es todo!
```

### **Usuarios Avanzados:**
```bash
python main.py --cli /mi/directorio/ --recursive --confidence 0.4
```

### **Administradores de Sistema:**
```bash
python main.py --batch /servidor/musica/ --workers 16 --dry-run
```

---

**El launcher unificado simplifica y mejora toda la experiencia de uso del sistema de detección de géneros musicales.** 🎵 