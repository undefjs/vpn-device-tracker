# Estructura del Componente VPN Device Tracker

```
custom_components/vpn_device_tracker/
├── __init__.py              # Entry point de la integración
├── config_flow.py           # Configuración UI (Config Flow)
├── const.py                 # Constantes compartidas
├── device_tracker.py        # Plataforma device_tracker
├── manifest.json            # Metadatos de la integración
├── strings.json             # Textos UI en inglés
└── translations/
    └── es.json              # Textos UI en español
```

## Archivos Principales

### `__init__.py`
- Gestiona el ciclo de vida de la integración
- Carga la plataforma device_tracker
- Maneja setup y unload

### `config_flow.py`
- Proporciona interfaz UI para configuración
- Valida entidades y rangos IP
- Crea entries de configuración

### `device_tracker.py`
- TrackerEntity que monitorea IPs
- Actualiza ubicación en tiempo real
- Soporta múltiples zonas

### `manifest.json`
- Metadatos de la integración
- `config_flow: true` para soporte UI

## Cómo Configurar

1. **Instalar** el componente en `custom_components/vpn_device_tracker`
2. **Reiniciar** Home Assistant
3. **Ir a** Configuración → Dispositivos y Servicios
4. **Añadir** integ ración "VPN Device Tracker"
5. **Configurar**:
   - Entidad origen: `device_tracker.tu_dispositivo`
   - Zonas IP (una por línea):
     ```
     home: 192.168.1.0/24
     office: 10.20.0.0/16
     ```

## Diferencias con Configuración YAML

❌ **YA NO SE PUEDE USAR** configuración YAML como:
```yaml
device_tracker:
  - platform: vpn_device_tracker  # ESTO NO FUNCIONA
```

✅ **AHORA SE USA** configuración UI desde la interfaz de Home Assistant
