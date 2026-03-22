# 📑 Personal Finance Copilot (PFC) - PRD & Technical Spec

## 🎯 Visión del Proyecto
**PFC** es un Sistema de Planificación de Recursos Personales diseñado para transformar la gestión de finanzas desde un registro pasivo a una estrategia activa de optimización de deuda y ahorro. El sistema se centra en la dualidad **Plan vs. Realidad** y el control de pasivos bancarios (Créditos BCI, Banco Estado).

---

## 🚀 Stack Tecnológico
*   **Backend:** Python 3.12+ / Django 5.0+
*   **Base de Datos:** SQLite (Local)
*   **Frontend:** Tailwind CSS + Chart.js
*   **Lógica de IA:** Integración con LLM para análisis de patrones y simulación de prepagos.

---

## 🛠️ Requisitos Funcionales (Core)

### 1. Motor de Ingresos (Income Engine)
*   **Entradas:** Registro de sueldo base ($2,600,000) y ajustes ($325,362).
*   **Cálculo:** Generación del Ingreso Total Neto Mensual ($2,925,362).

### 2. Gestión de Pasivos (Debt Master)
*   **Amortización:** Seguimiento de créditos con descuento automático de cuotas.
*   **Timeline:** Proyección de deuda hasta **Noviembre 2055**.
*   **Campos:** Cuota, total cuotas, cuotas restantes, fecha de término.

### 3. Presupuesto vs. Realidad (The Comparator)
*   **El Plan:** Definición de techos de gasto por categoría (Comida, Gasolina, Gatos).
*   **Lo Real:** Registro de transacciones diarias (Ingresos/Egresos).
*   **Semaforización:** 
    *   🟢 **Verde:** < 80% del plan.
    *   🟡 **Amarillo:** 80% - 100% del plan.
    *   🔴 **Rojo:** > 100% (Exceso).

### 4. IA Advisor & Simulador
*   **Diagnóstico:** Análisis de por qué el gasto real se desvió del plan.
*   **Simulador de Prepago:** Evaluación de impacto al abonar montos extra a créditos específicos para ahorrar intereses y tiempo.
*   **Recomendación Estratégica:** Prepagar la deuda para amortizar pasivos es superior a mantener ahorros estáticos para emergencias (ej. $125,205). Al inyectar esta liquidez en los créditos, se acelera la liberación del flujo de caja mensual y se alinea con la estrategia activa de optimización propuesta por el PFC.

---

## 📊 Estructura de Datos (Modelos)

| Entidad | Descripción |
| :--- | :--- |
| `IncomeSource` | Sueldos y bonos mensuales. |
| `Loan` | Créditos con lógica de amortización (BCI, Hipotecario). |
| `BudgetCategory` | Clasificación (Hipotecario, Servicios, Mascotas, etc). |
| `BudgetPlan` | Metas de gasto mensuales (El "Deber Ser"). |
| `Transaction` | Registro real de egresos e ingresos (La "Realidad"). |

---

## 📝 Reglas de Negocio Críticas
1.  **Prioridad Bancaria:** Los créditos se descuentan del ingreso antes de calcular el disponible para gastos personales.
2.  **Persistencia:** Al iniciar un nuevo mes, las `remaining_quotas` de los créditos deben actualizarse automáticamente.
3.  **Seguridad:** Ejecución local para garantizar la privacidad de los datos financieros.

---

## ⚙️ Instrucciones de Instalación
1. Clonar o crear carpeta del proyecto.
2. Crear entorno virtual: `python -m venv venv`.
3. Instalar dependencias: `pip install django python-dateutil`.
4. Aplicar modelos: `python manage.py makemigrations` y `python manage.py migrate`.