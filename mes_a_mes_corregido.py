# ============================================
# 📊 ANÁLISIS DE HORARIOS - KINGCHOLAO
# ============================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

print("="*60)
print("📊 ANÁLISIS DE HORARIOS - KINGCHOLAO")
print("="*60)

# ============================================
# 1. PREPARAR DATOS DE HORA
# ============================================

# Verificar que existe la columna 'hora'
if 'hora' not in df.columns:
    print("❌ No se encontró la columna 'hora'")
    print("📋 Columnas disponibles:", list(df.columns))
    # Buscar columnas similares
    for col in df.columns:
        if 'hora' in col.lower():
            print(f"   ¿Quisiste usar '{col}'?")
    exit()

print("\n⏰ Procesando datos de hora...")

# Convertir hora a formato datetime
df['hora_dt'] = pd.to_datetime(df['hora'], format='%H:%M:%S', errors='coerce')

# Si falla, intentar extraer solo la hora
if df['hora_dt'].isna().all():
    print("   ⚠️ Formato de hora no estándar, extrayendo hora...")
    df['hora_num'] = df['hora'].astype(str).str.split(':').str[0].astype(float)
else:
    df['hora_num'] = df['hora_dt'].dt.hour + df['hora_dt'].dt.minute/60

# Filtrar horas válidas (6 AM a 11 PM)
df_horas = df[(df['hora_num'] >= 6) & (df['hora_num'] <= 23)].copy()
print(f"✅ Horas procesadas: {len(df_horas):,} registros")

# ============================================
# 2. ANÁLISIS POR HORA
# ============================================
print("\n" + "="*60)
print("📊 VENTAS POR HORA")
print("="*60)

# Agrupar por hora
ventas_por_hora = df_horas.groupby(df_horas['hora_num'].astype(int))['total'].sum()
facturas_por_hora = df_horas.groupby(df_horas['hora_num'].astype(int))['idfactura'].count()
promedio_por_hora = ventas_por_hora / facturas_por_hora

# Mostrar todas las horas
print("\n📋 VENTAS POR HORA (TODOS LOS DÍAS):")
print("-"*50)
for hora in range(6, 24):
    if hora in ventas_por_hora.index:
        ventas = ventas_por_hora[hora]
        facturas = facturas_por_hora[hora]
        promedio = promedio_por_hora[hora]
        print(f"   {hora:02d}:00 - ${ventas:,.2f} ({facturas:.0f} facturas) - Promedio: ${promedio:,.2f}")
    else:
        print(f"   {hora:02d}:00 - Sin datos")

# ============================================
# 3. TOP HORAS
# ============================================
print("\n" + "="*60)
print("🏆 TOP 10 HORAS CON MÁS VENTAS")
print("="*60)

top_horas = ventas_por_hora.sort_values(ascending=False).head(10)
for i, (hora, monto) in enumerate(top_horas.items(), 1):
    facturas = facturas_por_hora[hora]
    promedio = promedio_por_hora[hora]
    print(f"   {i:2d}. {hora:02d}:00 - ${monto:,.2f} ({facturas:.0f} facturas) - Promedio: ${promedio:,.2f}")

# ============================================
# 4. HORAS CON MENOS VENTAS
# ============================================
print("\n" + "="*60)
print("⏰ HORAS CON MENOS VENTAS (Posibles para cerrar)")
print("="*60)

horas_bajas = ventas_por_hora.sort_values().head(5)
for hora, monto in horas_bajas.items():
    facturas = facturas_por_hora[hora]
    promedio = promedio_por_hora[hora]
    print(f"   {hora:02d}:00 - ${monto:,.2f} ({facturas:.0f} facturas) - Promedio: ${promedio:,.2f}")

# ============================================
# 5. ANÁLISIS POR FRANJAS HORARIAS
# ============================================
print("\n" + "="*60)
print("📅 ANÁLISIS POR FRANJAS HORARIAS")
print("="*60)

def get_franja(hora):
    if pd.isna(hora):
        return "Sin hora"
    elif 6 <= hora < 9: return "Madrugada (6-9)"
    elif 9 <= hora < 12: return "Mañana (9-12)"
    elif 12 <= hora < 15: return "Mediodía (12-15)"
    elif 15 <= hora < 18: return "Tarde (15-18)"
    elif 18 <= hora < 21: return "Noche (18-21)"
    elif 21 <= hora < 24: return "Noche avanzada (21-24)"
    else: return "Madrugada (0-6)"

df_horas['franja'] = df_horas['hora_num'].apply(get_franja)

franjas = df_horas.groupby('franja').agg({
    'total': 'sum',
    'idfactura': 'count'
}).sort_values('total', ascending=False)

print("\n📊 VENTAS POR FRANJA HORARIA:")
print("-"*50)
for franja, row in franjas.iterrows():
    if franja != "Sin hora":
        porcentaje = (row['total'] / ventas_totales) * 100
        print(f"   {franja}: ${row['total']:,.2f} ({row['idfactura']:.0f} facturas) - {porcentaje:.1f}% del total")

# ============================================
# 6. RECOMENDACIÓN DE HORARIO
# ============================================
print("\n" + "="*60)
print("💡 RECOMENDACIÓN DE HORARIO PARA 42 HORAS SEMANALES")
print("="*60)

# Calcular estadísticas
total_ventas_horas = ventas_por_hora.sum()
horas_con_ventas = len([h for h in ventas_por_hora.index if ventas_por_hora[h] > 0])
promedio_ventas_hora = total_ventas_horas / horas_con_ventas if horas_con_ventas > 0 else 0

print(f"\n📊 Estadísticas de horarios:")
print(f"   • Total de horas con ventas: {horas_con_ventas}")
print(f"   • Promedio de ventas por hora: ${promedio_ventas_hora:,.2f}")

# Identificar horas pico y valle
horas_pico = ventas_por_hora.sort_values(ascending=False).head(3)
horas_valle = ventas_por_hora.sort_values().head(3)

print(f"\n📈 Horas PICO (NO cerrar):")
for hora, monto in horas_pico.items():
    facturas = facturas_por_hora[hora]
    print(f"   • {hora:02d}:00 - ${monto:,.2f} ({facturas:.0f} facturas)")

print(f"\n📉 Horas VALLE (Posibles para cerrar):")
for hora, monto in horas_valle.items():
    facturas = facturas_por_hora[hora]
    print(f"   • {hora:02d}:00 - ${monto:,.2f} ({facturas:.0f} facturas)")

# ============================================
# 7. CALCULAR HORAS ÓPTIMAS
# ============================================
print("\n" + "="*60)
print("⏰ CÁLCULO DE HORAS ÓPTIMAS")
print("="*60)

# Calcular el promedio de ventas por hora en cada franja
ventas_por_hora_agrupadas = df_horas.groupby(df_horas['hora_num'].astype(int))['total'].sum()
horas_ordenadas = ventas_por_hora_agrupadas.sort_values(ascending=False)

# Seleccionar las 42 horas más productivas de la semana
# (6 días x 7 horas = 42 horas)
horas_seleccionadas = horas_ordenadas.head(42).index.tolist()
horas_seleccionadas.sort()

print(f"\n📋 Las 42 horas más productivas de la semana son:")
print("-"*40)
for i, hora in enumerate(horas_seleccionadas, 1):
    monto = ventas_por_hora[hora] if hora in ventas_por_hora.index else 0
    facturas = facturas_por_hora[hora] if hora in facturas_por_hora.index else 0
    print(f"   {i:2d}. {hora:02d}:00 - ${monto:,.2f} ({facturas:.0f} facturas)")

# ============================================
# 8. VISUALIZACIONES
# ============================================
print("\n📈 Generando gráficos de horarios...")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('📊 ANÁLISIS DE HORARIOS - KINGCHOLAO', fontsize=16, fontweight='bold')

# Gráfico 1: Ventas por hora
horas = sorted([h for h in ventas_por_hora.index if not pd.isna(h)])
valores = [ventas_por_hora[h] for h in horas]

axes[0,0].bar(horas, valores, color='skyblue', edgecolor='navy')
axes[0,0].set_title('💰 Ventas por Hora del Día', fontweight='bold')
axes[0,0].set_xlabel('Hora')
axes[0,0].set_ylabel('Ventas ($)')
axes[0,0].set_xticks(range(6, 24, 2))
axes[0,0].grid(axis='y', alpha=0.3)

# Gráfico 2: Facturas por hora
facturas_lista = [facturas_por_hora[h] if h in facturas_por_hora.index else 0 for h in horas]
axes[0,1].bar(horas, facturas_lista, color='lightcoral', edgecolor='darkred')
axes[0,1].set_title('📄 Facturas por Hora del Día', fontweight='bold')
axes[0,1].set_xlabel('Hora')
axes[0,1].set_ylabel('Número de Facturas')
axes[0,1].set_xticks(range(6, 24, 2))
axes[0,1].grid(axis='y', alpha=0.3)

# Gráfico 3: Promedio por hora
promedio_lista = [promedio_por_hora[h] if h in promedio_por_hora.index else 0 for h in horas]
axes[1,0].bar(horas, promedio_lista, color='lightgreen', edgecolor='darkgreen')
axes[1,0].set_title('📊 Promedio por Factura por Hora', fontweight='bold')
axes[1,0].set_xlabel('Hora')
axes[1,0].set_ylabel('Promedio ($)')
axes[1,0].set_xticks(range(6, 24, 2))
axes[1,0].grid(axis='y', alpha=0.3)

# Gráfico 4: Ventas por franja horaria
franjas_ordenadas = franjas[franjas.index != 'Sin hora']
nombres_franjas = franjas_ordenadas.index.tolist()
valores_franjas = franjas_ordenadas['total'].tolist()

axes[1,1].pie(valores_franjas, labels=nombres_franjas, autopct='%1.1f%%', 
              colors=['#4CAF50', '#FFC107', '#FF6B6B', '#45B7D1', '#96CEB4'])
axes[1,1].set_title('Distribución de Ventas por Franja Horaria', fontweight='bold')

plt.tight_layout()
plt.show()

# ============================================
# 9. RECOMENDACIÓN FINAL
# ============================================
print("\n" + "="*60)
print("💡 RECOMENDACIÓN FINAL DE HORARIO")
print("="*60)

# Calcular el horario óptimo
if len(horas_seleccionadas) >= 7:
    hora_apertura = min(horas_seleccionadas)
    hora_cierre = max(horas_seleccionadas)
    
    print(f"\n🏪 HORARIO RECOMENDADO:")
    print(f"   • Apertura: {hora_apertura:02d}:00 AM")
    print(f"   • Cierre: {hora_cierre:02d}:00 PM")
    print(f"   • Horas diarias: {hora_cierre - hora_apertura} horas")
    print(f"   • Días a la semana: 6 días")
    print(f"   • Total semanal: {(hora_cierre - hora_apertura) * 6} horas")
    
    # Identificar las horas menos productivas para considerar cierre
    print(f"\n⚠️ HORAS MENOS PRODUCTIVAS (Considerar cerrar):")
    for hora, monto in horas_bajas.items():
        facturas = facturas_por_hora[hora] if hora in facturas_por_hora.index else 0
        print(f"   • {hora:02d}:00 - ${monto:,.2f} ({facturas:.0f} facturas)")
    
    print(f"\n💡 ESTRATEGIA DE 42 HORAS SEMANALES:")
    print(f"   • Opción 1: {hora_apertura:02d}:00 a {hora_cierre:02d}:00, 6 días a la semana")
    print(f"   • Opción 2: 8:00 AM a 3:00 PM, 6 días a la semana (48 horas)")
    print(f"   • Opción 3: 10:00 AM a 5:00 PM, 6 días a la semana (42 horas)")
    
    print(f"\n📈 IMPACTO DE CADA OPCIÓN:")
    print(f"   • Opción 1: Cubre el {sum(ventas_por_hora[h] for h in range(hora_apertura, hora_cierre+1) if h in ventas_por_hora.index) / total_ventas_horas * 100:.1f}% de las ventas")
    print(f"   • Opción 2: Cubre el {sum(ventas_por_hora[h] for h in range(8, 16) if h in ventas_por_hora.index) / total_ventas_horas * 100:.1f}% de las ventas")
    print(f"   • Opción 3: Cubre el {sum(ventas_por_hora[h] for h in range(10, 18) if h in ventas_por_hora.index) / total_ventas_horas * 100:.1f}% de las ventas")

print("\n" + "="*60)
print("✅ ANÁLISIS DE HORARIOS COMPLETADO")
print("="*60)
