#!/usr/bin/env python3
"""
🌐 HTTP CLIENT - NUEVA BIBLIOTECA v2.0
=====================================
Cliente HTTP robusto con retry, timeout y manejo de errores
"""

import time
import json
import logging
from typing import Dict, Any, Optional, Union
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import ssl

logger = logging.getLogger(__name__)

class HTTPClient:
    """
    Cliente HTTP robusto con funcionalidades avanzadas:
    - Retry automático con backoff exponencial
    - Timeout configurable
    - Manejo de errores HTTP
    - Headers personalizables
    - Soporte para SSL/TLS
    """
    
    def __init__(self, 
                 timeout: int = 30,
                 max_retries: int = 3,
                 backoff_factor: float = 1.0,
                 user_agent: str = "Nueva-Biblioteca/2.0"):
        """
        Inicializar el cliente HTTP.
        
        Args:
            timeout: Timeout en segundos para las requests
            max_retries: Número máximo de reintentos
            backoff_factor: Factor de backoff exponencial
            user_agent: User-Agent string
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_factor = backoff_factor
        self.user_agent = user_agent
        
        # Headers por defecto
        self.default_headers = {
            'User-Agent': self.user_agent,
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive'
        }
        
        # Configurar SSL context
        self.ssl_context = ssl.create_default_context()
        
    def _prepare_request(self, 
                        url: str, 
                        method: str = 'GET',
                        headers: Optional[Dict[str, str]] = None,
                        data: Optional[Union[str, bytes, Dict[str, Any]]] = None) -> Request:
        """
        Preparar objeto Request con headers y datos.
        
        Args:
            url: URL de destino
            method: Método HTTP (GET, POST, etc.)
            headers: Headers adicionales
            data: Datos para el body (POST/PUT)
            
        Returns:
            Objeto Request configurado
        """
        # Combinar headers
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)
            
        # Preparar datos
        request_data = None
        if data is not None:
            if isinstance(data, dict):
                # Convertir dict a JSON
                request_data = json.dumps(data).encode('utf-8')
                request_headers['Content-Type'] = 'application/json'
            elif isinstance(data, str):
                request_data = data.encode('utf-8')
            else:
                request_data = data
                
        # Crear request
        req = Request(url, data=request_data, headers=request_headers)
        req.get_method = lambda: method
        
        return req
        
    def _should_retry(self, error: Exception, attempt: int) -> bool:
        """
        Determinar si se debe reintentar la request.
        
        Args:
            error: Excepción ocurrida
            attempt: Número de intento actual
            
        Returns:
            True si se debe reintentar, False si no
        """
        if attempt >= self.max_retries:
            return False
            
        # Reintentar en errores de red
        if isinstance(error, URLError):
            return True
            
        # Reintentar en ciertos códigos HTTP
        if isinstance(error, HTTPError):
            retry_codes = {429, 500, 502, 503, 504}
            return error.code in retry_codes
            
        return False
        
    def _calculate_backoff(self, attempt: int) -> float:
        """
        Calcular tiempo de espera para backoff exponencial.
        
        Args:
            attempt: Número de intento
            
        Returns:
            Tiempo de espera en segundos
        """
        return self.backoff_factor * (2 ** attempt)
        
    def request(self, 
               url: str,
               method: str = 'GET',
               headers: Optional[Dict[str, str]] = None,
               data: Optional[Union[str, bytes, Dict[str, Any]]] = None,
               params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Realizar request HTTP con retry automático.
        
        Args:
            url: URL de destino
            method: Método HTTP
            headers: Headers adicionales
            data: Datos para el body
            params: Parámetros de query string
            
        Returns:
            Diccionario con respuesta parseada
            
        Raises:
            HTTPError: Error HTTP no recuperable
            URLError: Error de red no recuperable
            ValueError: Error de parsing JSON
        """
        # Añadir parámetros a la URL si existen
        if params:
            separator = '&' if '?' in url else '?'
            url = f"{url}{separator}{urlencode(params)}"
            
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                # Preparar request
                req = self._prepare_request(url, method, headers, data)
                
                # Realizar request
                logger.debug(f"HTTP {method} {url} (attempt {attempt + 1})")
                
                with urlopen(req, timeout=self.timeout, context=self.ssl_context) as response:
                    # Leer respuesta
                    response_data = response.read()
                    
                    # Decodificar si es necesario
                    if isinstance(response_data, bytes):
                        response_data = response_data.decode('utf-8')
                        
                    # Parsear JSON si es posible
                    try:
                        parsed_data = json.loads(response_data)
                    except json.JSONDecodeError:
                        # Si no es JSON válido, devolver como texto
                        parsed_data = {'text': response_data}
                        
                    # Añadir metadatos de respuesta
                    result = {
                        'data': parsed_data,
                        'status_code': response.getcode(),
                        'headers': dict(response.headers),
                        'url': response.geturl()
                    }
                    
                    logger.debug(f"HTTP {method} {url} -> {result['status_code']}")
                    return result
                    
            except (HTTPError, URLError) as e:
                last_error = e
                
                # Log del error
                if isinstance(e, HTTPError):
                    logger.warning(f"HTTP {e.code} error for {url}: {e.reason}")
                else:
                    logger.warning(f"Network error for {url}: {e.reason}")
                
                # Verificar si se debe reintentar
                if not self._should_retry(e, attempt):
                    break
                    
                # Esperar antes del siguiente intento
                if attempt < self.max_retries:
                    backoff_time = self._calculate_backoff(attempt)
                    logger.info(f"Retrying in {backoff_time:.2f} seconds...")
                    time.sleep(backoff_time)
                    
            except Exception as e:
                logger.error(f"Unexpected error for {url}: {e}")
                last_error = e
                break
                
        # Si llegamos aquí, todos los intentos fallaron
        if last_error:
            raise last_error
        else:
            raise URLError("All retry attempts failed")
            
    def get(self, url: str, 
            headers: Optional[Dict[str, str]] = None,
            params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Realizar GET request.
        
        Args:
            url: URL de destino
            headers: Headers adicionales
            params: Parámetros de query string
            
        Returns:
            Diccionario con respuesta
        """
        return self.request(url, 'GET', headers=headers, params=params)
        
    def post(self, url: str,
             data: Optional[Union[str, bytes, Dict[str, Any]]] = None,
             headers: Optional[Dict[str, str]] = None,
             params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Realizar POST request.
        
        Args:
            url: URL de destino
            data: Datos para el body
            headers: Headers adicionales
            params: Parámetros de query string
            
        Returns:
            Diccionario con respuesta
        """
        return self.request(url, 'POST', headers=headers, data=data, params=params)
        
    def put(self, url: str,
            data: Optional[Union[str, bytes, Dict[str, Any]]] = None,
            headers: Optional[Dict[str, str]] = None,
            params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Realizar PUT request.
        
        Args:
            url: URL de destino
            data: Datos para el body
            headers: Headers adicionales
            params: Parámetros de query string
            
        Returns:
            Diccionario con respuesta
        """
        return self.request(url, 'PUT', headers=headers, data=data, params=params)
        
    def delete(self, url: str,
               headers: Optional[Dict[str, str]] = None,
               params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Realizar DELETE request.
        
        Args:
            url: URL de destino
            headers: Headers adicionales
            params: Parámetros de query string
            
        Returns:
            Diccionario con respuesta
        """
        return self.request(url, 'DELETE', headers=headers, params=params)
        
    def set_timeout(self, timeout: int) -> None:
        """
        Actualizar timeout para requests.
        
        Args:
            timeout: Nuevo timeout en segundos
        """
        self.timeout = timeout
        
    def set_user_agent(self, user_agent: str) -> None:
        """
        Actualizar User-Agent string.
        
        Args:
            user_agent: Nuevo User-Agent
        """
        self.user_agent = user_agent
        self.default_headers['User-Agent'] = user_agent
        
    def add_default_header(self, key: str, value: str) -> None:
        """
        Añadir header por defecto.
        
        Args:
            key: Nombre del header
            value: Valor del header
        """
        self.default_headers[key] = value
        
    def remove_default_header(self, key: str) -> None:
        """
        Remover header por defecto.
        
        Args:
            key: Nombre del header a remover
        """
        self.default_headers.pop(key, None)
        
    def get_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas del cliente.
        
        Returns:
            Diccionario con configuración actual
        """
        return {
            'timeout': self.timeout,
            'max_retries': self.max_retries,
            'backoff_factor': self.backoff_factor,
            'user_agent': self.user_agent,
            'default_headers': self.default_headers.copy()
        }