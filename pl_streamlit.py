import streamlit as st
import pandas as pd
import numpy as np
from scipy.optimize import linprog
import plotly.express as px
import plotly.graph_objects as go

# Configuración de la página
st.set_page_config(
    page_title="Optimización de Portafolio - Heinlein and Krampf",
    page_icon="📈",
    layout="wide"
)

# Título y descripción
st.title("📊 Optimización de Cartera de Inversiones")
st.markdown("""
### Heinlein and Krampf - Asignación de $250,000
Este aplicativo resuelve el problema de selección de portafolio utilizando Programación Lineal,
maximizando el rendimiento sujeto a las restricciones del cliente.
""")

# Sidebar para parámetros
with st.sidebar:
    st.header("⚙️ Parámetros de Inversión")
    
    # Capital total
    capital_total = st.number_input(
        "Capital total a invertir ($)",
        min_value=10000,
        max_value=1000000,
        value=250000,
        step=10000,
        format="%d"
    )
    
    st.subheader("📌 Restricciones del Cliente")
    
    # Restricción (a)
    min_bonos_pct = st.slider(
        "(a) % mínimo en Bonos Municipales",
        min_value=0,
        max_value=50,
        value=20,
        help="Los bonos municipales deben constituir al menos este porcentaje"
    ) / 100
    
    # Restricción (b)
    min_tec_pct = st.slider(
        "(b) % mínimo en Electrónica + Aeroespacial + Medicamentos",
        min_value=0,
        max_value=100,
        value=40,
        help="Al menos este porcentaje en combinación de estos sectores"
    ) / 100
    
    # Restricción (c)
    max_happy_pct_bonos = st.slider(
        "(c) % máximo de Bonos que puede ir a Happy Days",
        min_value=0,
        max_value=100,
        value=50,
        help="No más de este porcentaje de los bonos puede ir a Happy Days"
    ) / 100
    
    st.subheader("💰 Tasas de Rendimiento (%)")
    
    # Tasas de rendimiento editables
    tasa_bonos = st.number_input("Bonos Municipales LA", value=5.3, step=0.1, format="%.1f") / 100
    tasa_thompson = st.number_input("Electrónica Thompson", value=6.8, step=0.1, format="%.1f") / 100
    tasa_aero = st.number_input("Corp. Aeroespacial Unida", value=4.9, step=0.1, format="%.1f") / 100
    tasa_palmer = st.number_input("Medicamentos Palmer", value=8.4, step=0.1, format="%.1f") / 100
    tasa_happy = st.number_input("Hogares Happy Days", value=11.8, step=0.1, format="%.1f") / 100
    
    # Botón para resolver
    resolver = st.button("🚀 Resolver Optimización", type="primary", use_container_width=True)

# Definición de inversiones
inversiones = [
    "Bonos Municipales LA",
    "Electrónica Thompson",
    "Corp. Aeroespacial Unida",
    "Medicamentos Palmer",
    "Hogares Happy Days"
]

tasas = [tasa_bonos, tasa_thompson, tasa_aero, tasa_palmer, tasa_happy]

# Mostrar datos en columnas
col1, col2 = st.columns(2)

with col1:
    st.subheader("📋 Inversiones Disponibles")
    df_inversiones = pd.DataFrame({
        "Inversión": inversiones,
        "Tasa Rendimiento (%)": [t*100 for t in tasas]
    })
    st.dataframe(df_inversiones, use_container_width=True)

with col2:
    st.subheader("📐 Restricciones Aplicadas")
    st.info(f"""
    **a)** Bonos Municipales ≥ {min_bonos_pct*100:.1f}% → ${min_bonos_pct * capital_total:,.0f}
    
    **b)** Electrónica + Aeroespacial + Medicamentos ≥ {min_tec_pct*100:.1f}% → ${min_tec_pct * capital_total:,.0f}
    
    **c)** Happy Days ≤ {max_happy_pct_bonos*100:.1f}% de Bonos → x₅ ≤ {max_happy_pct_bonos:.2f} · x₁
    """)

# Resolver cuando se presiona el botón
if resolver:
    with st.spinner("Resolviendo modelo de optimización..."):
        
        # Coeficientes de la función objetivo (negativos porque linprog minimiza)
        c = [-t for t in tasas]
        
        # Matriz de restricciones de desigualdad (A_ub @ x <= b_ub)
        A_ub = []
        b_ub = []
        
        # Restricción (c): x5 <= 0.5*x1  =>  -0.5*x1 + x5 <= 0
        A_ub.append([-max_happy_pct_bonos, 0, 0, 0, 1])
        b_ub.append(0)
        
        # Restricción (a): x1 >= min_bonos_pct * capital
        # Convertir a <=: -x1 <= -min_bonos_pct * capital
        A_ub.append([-1, 0, 0, 0, 0])
        b_ub.append(-min_bonos_pct * capital_total)
        
        # Restricción (b): x2 + x3 + x4 >= min_tec_pct * capital
        # Convertir a <=: -x2 - x3 - x4 <= -min_tec_pct * capital
        A_ub.append([0, -1, -1, -1, 0])
        b_ub.append(-min_tec_pct * capital_total)
        
        # Restricción de igualdad: suma de inversiones = capital_total
        A_eq = [[1, 1, 1, 1, 1]]
        b_eq = [capital_total]
        
        # Límites de variables (no negativas)
        bounds = [(0, None) for _ in range(5)]
        
        # Resolver
        result = linprog(
            c=c,
            A_ub=A_ub,
            b_ub=b_ub,
            A_eq=A_eq,
            b_eq=b_eq,
            bounds=bounds,
            method='highs'
        )
        
        if result.success:
            # Resultados
            x_opt = result.x
            rendimiento_total = -result.fun
            rendimiento_pct = (rendimiento_total / capital_total) * 100
            
            # Mostrar resultados
            st.success("✅ Optimización completada exitosamente!")
            
            # Métricas principales
            col_metric1, col_metric2, col_metric3 = st.columns(3)
            with col_metric1:
                st.metric(
                    "Rendimiento Total Anual",
                    f"${rendimiento_total:,.2f}",
                    delta=None
                )
            with col_metric2:
                st.metric(
                    "Rendimiento Promedio",
                    f"{rendimiento_pct:.2f}%",
                    delta=None
                )
            with col_metric3:
                st.metric(
                    "Capital Invertido",
                    f"${capital_total:,.0f}",
                    delta=None
                )
            
            # Tabla de asignación
            st.subheader("📊 Asignación Óptima de Inversiones")
            
            df_result = pd.DataFrame({
                "Inversión": inversiones,
                "Monto Invertido ($)": x_opt,
                "Participación (%)": (x_opt / capital_total) * 100,
                "Rendimiento ($)": x_opt * tasas,
                "Tasa (%)": [t*100 for t in tasas]
            })
            
            # Formato
            df_result["Monto Invertido ($)"] = df_result["Monto Invertido ($)"].map("${:,.2f}".format)
            df_result["Participación (%)"] = df_result["Participación (%)"].map("{:.2f}%".format)
            df_result["Rendimiento ($)"] = df_result["Rendimiento ($)"].map("${:,.2f}".format)
            df_result["Tasa (%)"] = df_result["Tasa (%)"].map("{:.1f}%".format)
            
            st.dataframe(df_result, use_container_width=True)
            
            # Gráfico de pastel
            st.subheader("🥧 Distribución de la Cartera")
            
            fig_pie = px.pie(
                values=x_opt,
                names=inversiones,
                title="Composición del Portafolio Óptimo",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Set2
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
            
            # Gráfico de barras - Rendimiento por inversión
            st.subheader("📈 Rendimiento por Inversión")
            
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                x=inversiones,
                y=x_opt * np.array(tasas),
                text=[f"${v:,.0f}" for v in x_opt * np.array(tasas)],
                textposition='auto',
                marker_color='lightgreen',
                name='Rendimiento ($)'
            ))
            fig_bar.update_layout(
                title="Rendimiento Anual por Tipo de Inversión",
                xaxis_title="Inversión",
                yaxis_title="Rendimiento ($)",
                yaxis=dict(tickformat="$,.0f")
            )
            st.plotly_chart(fig_bar, use_container_width=True)
            
            # Verificación de restricciones
            st.subheader("✅ Verificación de Restricciones")
            
            col_v1, col_v2 = st.columns(2)
            
            with col_v1:
                st.write("**Restricción (a): Bonos Municipales**")
                bonos_inv = x_opt[0]
                bonos_min = min_bonos_pct * capital_total
                st.write(f"- Invertido en bonos: ${bonos_inv:,.2f}")
                st.write(f"- Mínimo requerido: ${bonos_min:,.2f}")
                if bonos_inv >= bonos_min - 1e-6:
                    st.success("✓ Cumple")
                else:
                    st.error("✗ No cumple")
            
            with col_v2:
                st.write("**Restricción (b): Electrónica + Aeroespacial + Medicamentos**")
                tec_inv = x_opt[1] + x_opt[2] + x_opt[3]
                tec_min = min_tec_pct * capital_total
                st.write(f"- Invertido en sector: ${tec_inv:,.2f}")
                st.write(f"- Mínimo requerido: ${tec_min:,.2f}")
                if tec_inv >= tec_min - 1e-6:
                    st.success("✓ Cumple")
                else:
                    st.error("✗ No cumple")
            
            st.write("**Restricción (c): Happy Days vs Bonos**")
            happy_inv = x_opt[4]
            happy_max = max_happy_pct_bonos * x_opt[0]
            st.write(f"- Invertido en Happy Days: ${happy_inv:,.2f}")
            st.write(f"- Máximo permitido ({max_happy_pct_bonos*100:.1f}% de bonos): ${happy_max:,.2f}")
            if happy_inv <= happy_max + 1e-6:
                st.success("✓ Cumple")
            else:
                st.error("✗ No cumple")
            
        else:
            st.error(f"❌ Error en la optimización: {result.message}")

else:
    st.info("👈 Ajusta los parámetros en la barra lateral y presiona 'Resolver Optimización'")

# Pie de página
st.markdown("---")
st.markdown("""
**Nota:** Este modelo utiliza Programación Lineal (método 'highs' de SciPy) para maximizar el rendimiento
sujeto a las restricciones del cliente. Los resultados son óptimos dentro de los parámetros establecidos.
""")

if __name__ == '__main__':

    st.set_option('server.enableCORS', False)
