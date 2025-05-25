#!/usr/bin/env python3
"""
Script para actualizar el estado del proyecto en McpServer Dart AI.
"""

import os
import json
import logging
import requests
from datetime import datetime
from typing import Dict, Any

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_config() -> Dict[str, Any]:
    """Carga la configuración de Dart MCP."""
    try:
        with open('dart_mcp_config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error cargando configuración: {str(e)}")
        raise

def load_update_data() -> Dict[str, Any]:
    """Carga los datos de actualización."""
    try:
        with open('dart_mcp_update.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error cargando datos de actualización: {str(e)}")
        raise

def send_update(config: Dict[str, Any], data: Dict[str, Any]) -> bool:
    """
    Envía la actualización a McpServer Dart AI.
    
    Args:
        config: Configuración de Dart MCP
        data: Datos a enviar
        
    Returns:
        bool: True si la actualización fue exitosa
    """
    try:
        # Obtener token
        token = os.getenv(config['dart_ai']['auth']['token_env'])
        if not token:
            raise ValueError("Token de autenticación no encontrado")
            
        # Preparar request
        headers = {
            'Authorization': f"Bearer {token}",
            'Content-Type': 'application/json'
        }
        
        endpoint = config['dart_ai']['endpoint']
        
        # Enviar actualización
        response = requests.post(
            endpoint,
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            logger.info("Actualización enviada exitosamente")
            return True
            
        else:
            logger.error(
                f"Error enviando actualización: {response.status_code}\n"
                f"Response: {response.text}"
            )
            return False
            
    except Exception as e:
        logger.error(f"Error en el proceso de actualización: {str(e)}")
        return False

def main():
    """Punto de entrada principal."""
    try:
        # Cargar configuración y datos
        config = load_config()
        data = load_update_data()
        
        # Actualizar timestamp
        config['project']['update_timestamp'] = (
            datetime.now().isoformat(timespec='seconds')
        )
        
        # Guardar configuración actualizada
        with open('dart_mcp_config.json', 'w') as f:
            json.dump(config, f, indent=4)
            
        # Enviar actualización
        if send_update(config, data):
            logger.info("Proceso de actualización completado")
            return 0
        else:
            logger.error("Error en el proceso de actualización")
            return 1
            
    except Exception as e:
        logger.error(f"Error crítico: {str(e)}")
        return 1

if __name__ == '__main__':
    exit(main())
