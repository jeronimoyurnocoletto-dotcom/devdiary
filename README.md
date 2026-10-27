# 🔐 Sprint 2: DevDiary (Usuarios y Seguridad)

La semana pasada tu diario aprendió a guardar entradas en una base de datos. Pero hay un problema: **cualquiera que abra la app ve las entradas de todos**.

Hoy vas a crear cuentas de usuario para que cada persona tenga su propio diario privado.

## 📁 Antes de empezar

Es el mismo DevDiary de la semana pasada, ahora con usuarios. Si no tienes las librerías instaladas:

```bash
python -m pip install -r requirements.txt
```

## 🧭 El mapa de hoy

```
Registro   →  guarda al usuario en la tabla User (con la contraseña cifrada)
Login      →  busca al usuario, compara la contraseña y lo recuerda en la session
El guardia →  antes de cada página privada revisa la session (ya viene hecho)
El diario  →  cada tarjeta tiene el correo de su dueño y cada quien ve solo las suyas
```

## 📋 Backlog del Sprint

Busca los comentarios `TICKET #...` y resuélvelos en orden:

- [ ] **TICKET #1: La tabla de usuarios (`main.py`)**
  - **Parte A:** completa la clase `User` con sus 3 columnas (`id`, `email`, `password`).
  - **Parte B:** reinicia la base de datos (mira el recuadro de abajo).
- [ ] **TICKET #2: Campo de contraseña (`login.html`)**
  - El formulario de login solo tiene el campo del correo. Crea el de la contraseña copiando su estructura.
- [ ] **TICKET #3: Registrar usuarios (`main.py`)**
  - En `reg_post`, crea el `User`, añádelo y confirma los cambios. Registra un usuario y revisa tu `diary.db`.
- [ ] **TICKET #4: Login y diario privado (`main.py`)**
  - **Parte A:** en `login_post`, busca al usuario, comprueba la contraseña y recuérdalo en la `session`.
  - **Parte B:** en `index`, trae solo las tarjetas de quien inició sesión.

> **Prueba final:** crea dos cuentas, escribe una entrada con cada una (usa el botón **Salir** para cambiar de cuenta) y comprueba que cada quien ve solo la suya.

### 🔄 Reiniciar la base de datos (Ticket #1, parte B)

Este sprint cambió la tabla `Card` (nueva columna `user_email`) y agregó la tabla `User`. Como `create_all()` nunca modifica una tabla que ya existe, hay que reiniciar:

1. Cuando termines la clase `User`, pon `RESET_DB = True` en `main.py`
2. Ejecuta la app **una sola vez**. Verás un aviso ⚠️ en la terminal.
3. Vuelve a poner `RESET_DB = False`

Si lo dejas en `True`, se borran los usuarios y las entradas cada vez que guardas un archivo.

---

## 📖 Chuleta

**Columnas**

| Código | Qué hace |
|---|---|
| `nullable=False` | El campo es obligatorio |
| `unique=True` | No se puede repetir (dos personas no pueden tener el mismo correo) |

**Consultas**

| Código | Qué hace |
|---|---|
| `User.query.filter_by(email=email)` | Filtra: solo los usuarios con ese correo |
| `.first()` | Trae **un** resultado, o `None` si no hay ninguno |
| `Card.query.filter_by(user_email=correo).order_by(...).all()` | Filtra primero y ordena después |

**Session (la memoria del navegador)**

| Código | Qué hace |
|---|---|
| `session['email'] = user.email` | Recuerda quién inició sesión |
| `session['email']` | Lee a quién recordamos |
| `session.pop('email', None)` | Lo olvida (cerrar sesión) |

**Contraseñas**

| Código | Qué hace |
|---|---|
| `generate_password_hash(password)` | Convierte la contraseña en un código ilegible |
| `check_password_hash(guardado, escrita)` | Compara; devuelve `True` o `False` |

---

## 🧠 Deep Dive: ¿Por qué no guardamos la contraseña tal cual?

Imagina que alguien consigue copiar tu `diary.db`. Si las contraseñas están escritas tal cual, esa persona entra a todas las cuentas. Y mucha gente usa la misma contraseña en varios sitios.

Por eso se guarda un **hash**: una huella de la contraseña que se puede calcular, pero **no se puede deshacer**. Es como una licuadora: convierte una fruta en jugo, pero no puedes volver a sacar la fruta.

¿Cómo sabe entonces `check_password_hash` si la contraseña es correcta? Cifra lo que escribiste ahora y compara las dos huellas.

Dos cosas para investigar en tu `diary.db`:
- El hash mide unos 160 caracteres. Por eso la columna `password` es `String(255)` y no `String(100)`.
- Registra dos usuarios con **la misma contraseña**. ¿Los hashes son iguales? (Spoiler: no. Python añade un valor aleatorio llamado *salt* a cada uno.)

---

## 🕵️ Experimentos de seguridad (si sobra tiempo)

1. **Sin iniciar sesión:** cierra sesión e intenta entrar a `http://127.0.0.1:5000/`. ¿Quién te detuvo? (Busca `guardia` en `main.py`.)
2. **Adivinar direcciones:** con la cuenta A, abre una de tus entradas y copia su dirección (algo como `/card/3`). Cierra sesión, entra con la cuenta B y pega esa dirección. ¿Qué pasa? ¿Qué líneas de `main.py` lo evitan? ¿Por qué no bastaba con filtrar en el índice?
3. **Mensaje de error:** prueba un correo que no existe y luego uno que existe con la contraseña equivocada. ¿El mensaje es distinto? ¿Por qué crees que es mejor que sea el mismo?

---

## 🆘 Errores comunes

| Si ves... | Significa | Solución |
|---|---|---|
| `could not assemble any primary key columns` | La clase `User` aún no tiene columnas | Termina el Ticket #1, parte A |
| `no such column: card.user_email` | Tu base de datos es la de la semana pasada | Ticket #1, parte B: `RESET_DB = True`, ejecuta una vez y vuelve a `False` |
| Tus usuarios y entradas desaparecen al guardar | Dejaste `RESET_DB = True` | Vuelve a ponerlo en `False` |
| Siempre sale "Correo o contraseña incorrectos" | El usuario no se guardó (Ticket #3) o falta tu `if` (Ticket #4) | Abre `diary.db` y revisa si existe en la tabla `user` |
| `'NoneType' object has no attribute 'password'` | Ese correo no existe y tu `if` no lo comprobó primero | Escribe `user and ...` antes de `check_password_hash` |
| Entras bien pero te devuelve al login | Falta guardar `session['email']` dentro de tu `if` | Revisa el Ticket #4, parte A |
| Sigues "dentro" después de reiniciar la base de datos | Tu navegador recuerda a un usuario que ya no existe | Entra a `/logout` y regístrate de nuevo |
