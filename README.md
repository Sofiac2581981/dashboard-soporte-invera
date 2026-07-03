# Dashboard de Reporting de Soporte — Invera

Dashboard de reporting para el equipo de Operaciones, construido a partir del dataset de
60 tickets de soporte (abr–jun 2026). Responde de un vistazo las 5 preguntas del líder del
equipo.

**Link en vivo:** _(pegar acá la URL de Streamlit Cloud una vez desplegado)_

---

## Cómo está pensado

El tablero no muestra "todos los gráficos posibles": está estructurado alrededor de las
5 preguntas de negocio, en orden, y termina con una conclusión accionable.

1. **¿Cuántos tickets hay y en qué estado?** → dona de estados + KPIs.
2. **¿Dónde están los cuellos de botella?** → resolución por categoría, respuesta vs
   resolución por prioridad, y desglose de bugs por subtipo.
3. **¿Qué clientes concentran carga y qué tan conformes están?** → burbujas carga vs
   satisfacción (tamaño = tiempo de resolución) + tabla con semáforo.
4. **¿El volumen crece, baja o está estable?** → serie semanal con promedio.
5. **¿Qué atender mañana?** → panel de alerta con las 3 prioridades + backlog actual.

## Hallazgos principales (lo que le diría al líder)

- **El 50% de los tickets son bugs** (30 de 60). Concentran la peor satisfacción (2.87 vs
  4.7 de Accesos), el peor tiempo de resolución (mediana 68 hs vs 14–24 hs del resto) y
  **el 100% de los escalados**. El 80% de los bugs termina escalado.
- **La primera respuesta está sana** (mediana 4 hs, máx 12). El cuello de botella no es
  atender, es **resolver bugs**.
- **Los 7 tickets sin cerrar son todos bugs de prioridad Alta.** El backlog es 100% bugs.
- **Quinto es el cliente en riesgo:** satisfacción 2.56/5 (la más baja por lejos) y el peor
  tiempo de resolución (63 hs). El resto de los clientes está entre 3.6 y 4.4.
- **El volumen es estable** (~5–6 tickets/semana). La caída de junio es un artefacto: el
  dataset corta el 12/06, media semana.

## Stack

- **Streamlit** (UI + hosting en Streamlit Community Cloud)
- **pandas** (carga y agregaciones)
- **Plotly** (gráficos interactivos)
- **openpyxl** (lectura del `.xlsx`)

## Correr localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy

Repo en GitHub → Streamlit Community Cloud → apuntar a `app.py`. El dataset
(`challenge-dataset-tickets.xlsx`) viaja versionado en el repo, así que no hay que subir
nada aparte.

---

## Proceso con IA (requisito del challenge)

**Herramienta:** Claude (Anthropic).

**Qué le pedí:**
1. Que analizara el dataset completo y me diera las respuestas a las 5 preguntas con
   números reales, antes de escribir una sola línea de dashboard. Quería que el criterio
   viniera de los datos, no de suponer.
2. Que eligiera el stack de deploy más simple para "abrí el link y funciona sin instalar
   nada" → propuso Streamlit Community Cloud, coincidí.
3. El código completo del dashboard, organizado por las 5 preguntas, con filtros y una
   conclusión accionable al final.

**Qué me devolvió mal y cómo lo corregí:**
- **Error de conteo de bugs.** En el primer pase reportó que los bugs eran el 38% de los
  tickets. Al validar los cálculos aislados me di cuenta de que ese 38% salía de contar
  **solo los tickets cerrados** (23 de 53). Como los 7 tickets abiertos son *todos* bugs,
  el número real sobre el total es **50% (30 de 60)**. Lo hice recalcular sobre el dataset
  completo. Moraleja: nunca tomar el primer número, siempre reproducir el cálculo.
- **Panel de alerta sensible a los filtros.** La primera versión calculaba la conclusión
  ("qué atender mañana") sobre el dataset filtrado, así que si alguien tocaba los filtros la
  conclusión se rompía. Lo cambié para que la sección 5 siempre se calcule sobre los 60
  tickets completos, y lo dejé aclarado con un caption.
- **Tentación de señalar a un agente.** Los datos muestran que un agente resuelve más
  rápido que otro. Al cruzar el mix de trabajo vi que ambos manejan la misma cantidad de
  bugs, así que la diferencia es ruido de asignación, no de performance. Decidí **dejarlo
  afuera** del dashboard para no sacar una conclusión injusta sobre una persona con 30
  tickets de muestra.

**Criterio propio sobre lo que dejé afuera:** no puse gráficos de "satisfacción por agente"
ni rankings de personas (muestra chica, conclusión riesgosa), ni un desglose de fechas de
cierre (agrega ruido sin responder ninguna de las 5 preguntas).
