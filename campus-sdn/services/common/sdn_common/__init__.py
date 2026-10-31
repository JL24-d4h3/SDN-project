"""Esqueleto compartido por los servicios de campus-sdn.

Lo común se escribe una sola vez (plan 09 §4): la fábrica de aplicaciones
con su /health, la construcción y validación de eventos del bus, y la
publicación con confirmación. Cada servicio aporta solo su lógica.
"""

__version__ = "0.1.0"
