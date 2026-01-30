# Widget Setup Guide - OBS & Browser

## Uso en OBS (Recomendado)

### Setup Rápido
1. En OBS: Sources → Add → Browser
2. URL: `http://tu-servidor:8000/widget`
3. Width: `1920`, Height: `1080`
4. **✅ Check:** "Shutdown source when not visible"
5. **✅ Check:** "Refresh browser when scene becomes active"
6. FPS: `30`

### Propiedades Importantes
```
URL: http://localhost:8000/widget
Width: 1920
Height: 1080
FPS: 30
☑ Shutdown source when not visible
☑ Refresh browser when scene becomes active
☐ Use custom frame rate (opcional)
☐ Control audio via OBS (opcional - si quieres controlar volumen desde OBS)
```

### Audio en OBS
**El audio funciona automáticamente en OBS** - No requiere interacción del usuario.

OBS usa CEF (Chromium Embedded Framework) que tiene autoplay habilitado por defecto.

## Query Parameters

### Basic
```
http://localhost:8000/widget
```

### Debug Mode
```
http://localhost:8000/widget?debug=true
```
Muestra info en pantalla:
- Platform (OBS/Browser)
- Audio/Visual queue size
- Status actual

### Sin Mensajes (Solo Alerts)
```
http://localhost:8000/widget?show_messages=false
```
Oculta mensajes TTS, solo muestra alerts de sub/follow.

### Combinado
```
http://localhost:8000/widget?debug=true&show_messages=false
```

## Testing sin OBS (Navegador)

### Problema: Autoplay Bloqueado
Los navegadores modernos (Chrome, Firefox, Safari) bloquean autoplay de audio por policy.

### Solución Automática
El widget detecta si NO está en OBS y muestra un overlay:
1. Se carga el widget
2. Llega el primer audio
3. Aparece overlay: "🔊 Habilitar Audio"
4. Click en botón
5. Audio funciona

### Testing Manual
```bash
# 1. Abrir widget
open http://localhost:8000/widget?debug=true

# 2. En otra terminal, enviar test
curl -X POST http://localhost:8000/api/test/subscription \
  -H "Content-Type: application/json" \
  -d '{"username":"TestUser"}'

# 3. Click en "Activar Audio" si aparece overlay
# 4. El audio debería reproducirse
```

## Arquitectura del Widget

### Detección de Plataforma
```javascript
// Auto-detecta OBS
const isOBS = /obs|cef/i.test(navigator.userAgent) || window.obsstudio !== undefined;

if (isOBS) {
    // Autoplay habilitado automáticamente
    audioUnlocked = true;
} else {
    // Browser normal - requiere interacción
    audioUnlocked = false;
}
```

### Colas Independientes

**Cola de Audio:**
```javascript
audioQueue = [sound1.mp3, sound2.mp3, subscription.mp3, ...]
```
- Se reproduce secuencialmente
- No se interrumpen
- Si un audio falla, continúa con el siguiente

**Cola Visual:**
```javascript
visualQueue = [
    {showFunction: showSubscription, duration: 7500},
    {showFunction: follow, duration: 6500},
    ...
]
```
- Se muestra uno tras otro
- No se superponen
- Auto-remove después de la duración

### Flow de Audio

```
1. Evento llega (subscription/follow/TTS)
   ↓
2. Se encola audio
   ↓
3. Si no está reproduciendo:
   ↓
4. ¿Es OBS? → Sí → Reproduce inmediatamente
   ↓        ↓ No
   ↓        ↓
   ↓        ¿Audio desbloqueado? → Sí → Reproduce
   ↓                              ↓ No
   ↓                              ↓
   ↓                              Muestra overlay
   ↓                              Espera click
   ↓                              Reproduce
5. Audio termina
   ↓
6. Siguiente en cola (volver a 4)
```

## Troubleshooting

### Audio no suena en OBS

**Check 1: Control Audio via OBS**
```
Right-click Browser Source → Properties
☐ Control audio via OBS (debe estar DESMARCADO)
```
O si está marcado:
```
OBS → Audio Mixer → Gear icon → Advanced Audio Properties
Browser Source → Volume: 100%
```

**Check 2: URL correcta**
```
✅ http://localhost:8000/widget
❌ file:///path/to/widget.html
```

**Check 3: Servidor corriendo**
```bash
curl http://localhost:8000/health
# Debe responder: {"status":"ok",...}
```

### Overlay aparece en OBS

Esto NO debería pasar. Si pasa:
1. Check navegador user agent en debug mode
2. Forzar detección OBS:
```
http://localhost:8000/widget?obs=true
```

### Audio se corta

**Problema:** Varios audios se encolan y se cortan.

**Causa:** Es correcto - es una cola secuencial.

**Solución:** Ajustar duración de mensajes o cooldown:
```bash
# .env
MAX_MESSAGE_LENGTH=100  # Mensajes más cortos
COOLDOWN_SECONDS=2      # Más tiempo entre mensajes
```

### Múltiples alerts superpuestos

**Problema:** Ver 3 alerts de subscription al mismo tiempo.

**Causa:** Cola visual no está funcionando.

**Check:** Debug mode debe mostrar `Visual Queue: 1+` cuando hay cola.

## Comparación con StreamElements/Streamlabs

### StreamElements
- Widget URL similar: `https://streamelements.com/overlay/...`
- Autoplay funciona en OBS
- Colas integradas
- **Diferencia:** Nuestro widget es self-hosted

### Streamlabs
- Widget URL: `https://streamlabs.com/widgets/...`
- Requiere login/API key
- Más features (donaciones, bits, etc)
- **Diferencia:** Nuestro widget es más simple, open source

### Nuestra Implementación
- ✅ Self-hosted (control total)
- ✅ Sin dependencias externas
- ✅ Funciona igual en OBS
- ✅ Modular para agregar eventos
- ⚠️ Menos features (por ahora)

## Best Practices

### Performance
```
Width: 1920
Height: 1080
FPS: 30 (no más)
```
Más FPS = más CPU usage sin beneficio visible.

### Scenes
```
☑ Shutdown source when not visible
```
Libera recursos cuando no está en scene activa.

### Testing
1. Test en navegador primero (debug=true)
2. Luego en OBS
3. Siempre test antes de ir live

### Updates
```bash
# Pull latest code
git pull

# Restart
docker-compose restart tts-bot

# Refresh en OBS: Right-click source → Refresh
```

## Advanced

### Custom CSS
Edita `templates/widget.html`:
```css
.message.subscription {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    /* Tu custom styling */
}
```

### Custom Sounds
```bash
# Agregar sonido
cp tu-sonido.mp3 static/sounds/

# Test
curl -X POST localhost:8000/api/play-sound \
  -H "Content-Type: application/json" \
  -d '{"sound_name":"tu-sonido"}'
```

### Multiple Instances
```
OBS Scene 1: http://localhost:8000/widget?show_messages=true
OBS Scene 2: http://localhost:8000/widget?show_messages=false
```
Diferentes configs en diferentes scenes.

## Summary

**En OBS:**
- Audio funciona automáticamente ✅
- No requiere overlay ni click ✅
- Usa CEF con autoplay enabled ✅

**En Navegador (testing):**
- Autoplay bloqueado por browser policy ⚠️
- Requiere overlay + click usuario ⚠️
- Solo para testing, no para producción ⚠️

**Producción = OBS = Todo automático ✅**
