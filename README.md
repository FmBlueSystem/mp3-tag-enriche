# Nueva Biblioteca

Sistema inteligente de gestión de bibliotecas musicales con filtros avanzados y playlists automáticas.

## Descripción

Aplicación de escritorio desarrollada en Python con PyQt6 que permite:

- **Gestión inteligente de metadatos**: Extracción y enriquecimiento automático de metadatos musicales
- **Motor de reglas avanzado**: Sistema de filtros con sintaxis natural para crear playlists dinámicas
- **Playlists inteligentes**: Generación automática basada en criterios personalizables
- **Exportación múltiple**: Soporte para M3U y otros formatos estándar
- **Interfaz moderna**: UI responsiva y fácil de usar

## Arquitectura Modular

```
src/
├── core/           # Motor principal y lógica de negocio
├── data/           # Persistencia y modelos de datos
├── ui/             # Interfaz de usuario PyQt6
├── apis/           # Integración con servicios externos
└── utils/          # Utilidades transversales
```

## Instalación

```bash
pip install -r requirements.txt
```

## Uso

```bash
python -m src
```

## Desarrollo

Este proyecto sigue las mejores prácticas de desarrollo Python:

- Tipado estático con mypy
- Tests con pytest
- Formateo con black
- Linting con flake8
- Documentación con Sphinx

## Licencia

MIT License
