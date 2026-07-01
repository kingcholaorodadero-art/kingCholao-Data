# ============================================================
# 📊 ANÁLISIS FINANCIERO - KING CHOLAO
# 📍 Google Colab - SCRIPT COMPLETO (612 LÍNEAS)
# 🔄 Filtra por año y genera PDF profesional
# ============================================================


# 2. IMPORTAR LIBRERÍAS
import pandas as pd
import numpy as np
import requests
import io
import os
import re
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
import matplotlib
matplotlib.use('Agg')

print("="*70)
print("📊 ANÁLISIS FINANCIERO - KING CHOLAO")
print("="*70)
print(f"📅 Fecha de ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)

# ============================================================
# CONFIGURACIÓN
# ============================================================
AÑO_FILTRO = 2026
REPO_OWNER = "kingcholaorodadero-art"
REPO_NAME = "kingCholao-Data"
DATA_PATH = "data_raw"

# ============================================================
# FUNCIONES DE EXTRACCIÓN
# ============================================================
def leer_archivo_github(file_info):
    try:
        resp = requests.get(file_info['download_url'], timeout=30)
        xls = pd.ExcelFile(io.BytesIO(resp.content))
        return xls
    except Exception as e:
        print(f"  ❌ Error al descargar: {e}")
        return None

def extraer_resumen_mes(xls, mes):
    try:
        if 'RESUMEN MES' not in xls.sheet_names:
            return None
        df = pd.read_excel(xls, sheet_name='RESUMEN MES', header=None)
        datos = {
            'Mes': mes,
            'Ventas_Efectivo': 0,
            'Ventas_Tarjeta': 0,
            'Ventas_Total': 0,
            'Gastos_Compras': 0,
            'Gastos_Personal': 0,
            'Gastos_Servicios': 0,
            'Gastos_Otros': 0,
            'Gastos_Total': 0,
            'Ganancia': 0,
            'Rentabilidad': 0,
            'Accesorios': 0
        }
        if len(df) > 5:
            for i, col in [(3, 'Ventas_Efectivo'), (4, 'Ventas_Tarjeta'), (5, 'Ventas_Total')]:
                if len(df) > i:
                    fila = df.iloc[i]
                    for x in fila:
                        if isinstance(x, (int, float)) and x > 0:
                            datos[col] = float(x)
                            break
        if len(df) > 12:
            fila = df.iloc[12]
            if len(fila) > 4:
                datos['Gastos_Compras'] = float(fila.iloc[4]) if isinstance(fila.iloc[4], (int, float)) and fila.iloc[4] != 0 else 0
            if len(fila) > 5:
                datos['Gastos_Personal'] = float(fila.iloc[5]) if isinstance(fila.iloc[5], (int, float)) and fila.iloc[5] != 0 else 0
            if len(fila) > 6:
                datos['Gastos_Servicios'] = float(fila.iloc[6]) if isinstance(fila.iloc[6], (int, float)) and fila.iloc[6] != 0 else 0
            if len(fila) > 7:
                datos['Gastos_Otros'] = float(fila.iloc[7]) if isinstance(fila.iloc[7], (int, float)) and fila.iloc[7] != 0 else 0
            if len(fila) > 8:
                datos['Gastos_Total'] = float(fila.iloc[8]) if isinstance(fila.iloc[8], (int, float)) and fila.iloc[8] != 0 else 0
            if datos['Gastos_Total'] == 0:
                datos['Gastos_Total'] = datos['Gastos_Compras'] + datos['Gastos_Personal'] + datos['Gastos_Servicios'] + datos['Gastos_Otros']
        if len(df) > 23:
            fila = df.iloc[23]
            if len(fila) > 3:
                x = fila.iloc[3]
                if isinstance(x, (int, float)):
                    datos['Ganancia'] = float(x)
            if len(fila) > 4:
                x = fila.iloc[4]
                if isinstance(x, (int, float)):
                    if x < 1:
                        datos['Rentabilidad'] = float(x) * 100
                    else:
                        datos['Rentabilidad'] = float(x)
        if datos['Ganancia'] == 0 and datos['Ventas_Total'] > 0 and datos['Gastos_Total'] > 0:
            datos['Ganancia'] = datos['Ventas_Total'] - datos['Gastos_Total']
            if datos['Ventas_Total'] > 0:
                datos['Rentabilidad'] = (datos['Ganancia'] / datos['Ventas_Total']) * 100
        return datos
    except Exception as e:
        print(f"  ⚠️ Error en {mes}: {e}")
        return None

def extraer_proveedores(xls, mes):
    try:
        hoja_egresos = None
        for sheet in xls.sheet_names:
            if 'EGRESOS' in sheet.upper():
                hoja_egresos = sheet
                break
        if hoja_egresos is None:
            return {}
        df = pd.read_excel(xls, sheet_name=hoja_egresos, header=None)
        header_row = None
        for i in range(min(15, len(df))):
            texto = ' '.join([str(x).lower() for x in df.iloc[i] if pd.notna(x)])
            if 'dia' in texto and 'tercero' in texto:
                header_row = i
                break
        if header_row is None:
            return {}
        headers = df.iloc[header_row].tolist()
        headers = [str(h).strip() if pd.notna(h) else f'Col_{j}' for j, h in enumerate(headers)]
        df_data = df.iloc[header_row + 1:].copy()
        df_data.columns = headers
        col_proveedor = None
        col_costo = None
        col_personal = None
        col_servicios = None
        col_otros = None
        for col in df_data.columns:
            col_upper = col.upper()
            if 'TERCERO' in col_upper:
                col_proveedor = col
            elif 'COSTOS' in col_upper and 'PERSONAL' not in col_upper and 'SERVICIOS' not in col_upper:
                col_costo = col
            elif 'PERSONAL' in col_upper:
                col_personal = col
            elif 'SERVICIOS' in col_upper:
                col_servicios = col
            elif 'OTROS' in col_upper:
                col_otros = col
        if col_proveedor is None:
            col_proveedor = df_data.columns[3] if len(df_data.columns) > 3 else None
        if col_costo is None:
            col_costo = df_data.columns[5] if len(df_data.columns) > 5 else None
        if col_personal is None:
            col_personal = df_data.columns[6] if len(df_data.columns) > 6 else None
        if col_servicios is None:
            col_servicios = df_data.columns[7] if len(df_data.columns) > 7 else None
        if col_otros is None:
            col_otros = df_data.columns[8] if len(df_data.columns) > 8 else None
        if col_proveedor is None:
            return {}
        for col in [col_costo, col_personal, col_servicios, col_otros]:
            if col and col in df_data.columns:
                df_data[col] = pd.to_numeric(df_data[col], errors='coerce')
        df_data['TOTAL'] = 0
        for col in [col_costo, col_personal, col_servicios, col_otros]:
            if col and col in df_data.columns:
                df_data['TOTAL'] += df_data[col].fillna(0)
        df_data = df_data[df_data[col_proveedor].notna()]
        df_data = df_data[df_data[col_proveedor].astype(str).str.strip() != '']
        df_data = df_data[df_data[col_proveedor].astype(str).str.strip() != 'nan']
        df_data = df_data[~df_data[col_proveedor].astype(str).str.contains('TOTALES|TOTAL MES|TOTAL', na=False, case=False)]
        df_data = df_data[df_data['TOTAL'] > 0]
        proveedores = {}
        for prov, monto in df_data.groupby(col_proveedor)['TOTAL'].sum().items():
            if pd.notna(prov) and str(prov).strip() and monto > 0:
                proveedores[str(prov).strip()] = float(monto)
        return proveedores
    except Exception as e:
        return {}

def extraer_ventas_diarias(xls):
    try:
        if 'VENTAS' not in xls.sheet_names:
            return {}
        df = pd.read_excel(xls, sheet_name='VENTAS', header=None)
        header_row = None
        for i in range(min(15, len(df))):
            texto = ' '.join([str(x).lower() for x in df.iloc[i] if pd.notna(x)])
            if 'dia' in texto and 'forma' in texto:
                header_row = i
                break
        if header_row is None:
            return {}
        headers = df.iloc[header_row].tolist()
        headers = [str(h).strip() if pd.notna(h) else f'Col_{j}' for j, h in enumerate(headers)]
        df_data = df.iloc[header_row + 1:].copy()
        df_data.columns = headers
        col_dia = None
        col_monto = None
        for col in df_data.columns:
            if 'DIA' in col.upper():
                col_dia = col
            if 'MONTO' in col.upper():
                col_monto = col
        if col_dia is None or col_monto is None:
            return {}
        df_data[col_monto] = pd.to_numeric(df_data[col_monto], errors='coerce')
        ventas = {}
        for dia, monto in df_data.groupby(col_dia)[col_monto].sum().items():
            if pd.notna(dia) and monto > 0:
                try:
                    ventas[int(dia)] = float(monto)
                except:
                    pass
        return ventas
    except Exception as e:
        return {}

# ============================================================
# PROCESAR ARCHIVOS
# ============================================================
print(f"\n📥 Conectando a GitHub (filtrando año {AÑO_FILTRO})...")
url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{DATA_PATH}"
response = requests.get(url).json()
archivos_excel = [f for f in response if f['name'].endswith('.xlsx')]

archivos_filtrados = []
for f in archivos_excel:
    if str(AÑO_FILTRO) in f['name']:
        archivos_filtrados.append(f)

print(f"✅ Encontrados {len(archivos_filtrados)} archivos para el año {AÑO_FILTRO}")

if not archivos_filtrados:
    print(f"❌ No se encontraron archivos para el año {AÑO_FILTRO}")
    exit()

print("\n" + "="*70)
print("📂 PROCESANDO ARCHIVOS")
print("="*70)

resultados = []

for file in archivos_filtrados:
    nombre = file['name']
    mes = re.sub(r'EGRESOS\s*', '', nombre).replace('.xlsx', '').strip()
    mes = re.sub(r'\s*\d{4}', '', mes).strip()
    print(f"\n📄 {nombre} -> {mes}")
    xls = leer_archivo_github(file)
    if xls is None:
        continue
    datos = extraer_resumen_mes(xls, mes + f" {AÑO_FILTRO}")
    if datos:
        datos['Proveedores'] = extraer_proveedores(xls, mes)
        datos['Ventas_Diarias'] = extraer_ventas_diarias(xls)
        resultados.append(datos)
        print(f"  ✅ Ventas: ${datos['Ventas_Total']:,.2f}")
        print(f"  ✅ Gastos: ${datos['Gastos_Total']:,.2f}")
        print(f"  ✅ Rentabilidad: {datos['Rentabilidad']:.2f}%")
        print(f"  ✅ Proveedores: {len(datos['Proveedores'])}")
    else:
        print(f"  ❌ No se pudieron extraer datos")

if not resultados:
    print("❌ No se procesó ningún archivo")
    exit()

# ============================================================
# CREAR DATAFRAME
# ============================================================
print("\n" + "="*70)
print("📊 CREANDO DATAFRAME")
print("="*70)

df = pd.DataFrame([{
    'Mes': r['Mes'],
    'Ventas_Efectivo': r.get('Ventas_Efectivo', 0),
    'Ventas_Tarjeta': r.get('Ventas_Tarjeta', 0),
    'Ventas_Total': r.get('Ventas_Total', 0),
    'Gastos_Compras': r.get('Gastos_Compras', 0),
    'Gastos_Personal': r.get('Gastos_Personal', 0),
    'Gastos_Servicios': r.get('Gastos_Servicios', 0),
    'Gastos_Otros': r.get('Gastos_Otros', 0),
    'Gastos_Total': r.get('Gastos_Total', 0),
    'Ganancia': r.get('Ganancia', 0),
    'Rentabilidad': r.get('Rentabilidad', 0),
    'Accesorios': r.get('Accesorios', 0)
} for r in resultados])

df = df.fillna(0)

orden_meses = ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO', 
               'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']

df['Mes_Solo'] = df['Mes'].str.replace(f' {AÑO_FILTRO}', '')
df['Mes_Orden'] = pd.Categorical(df['Mes_Solo'], categories=orden_meses, ordered=True)
df = df.sort_values('Mes_Orden').drop(['Mes_Orden', 'Mes_Solo'], axis=1)

print("\n📋 DATOS EXTRAÍDOS (ordenados):")
print(df.to_string(index=False, float_format=lambda x: f'{x:,.2f}'))

# ============================================================
# ANÁLISIS GENERAL
# ============================================================
print("\n" + "="*70)
print("📊 ANÁLISIS GENERAL")
print("="*70)

total_ventas = df['Ventas_Total'].sum()
total_gastos = df['Gastos_Total'].sum()
total_ganancia = df['Ganancia'].sum()
rentabilidad_promedio = df[df['Rentabilidad'] > 0]['Rentabilidad'].mean()

print(f"\n📈 TOTALES {AÑO_FILTRO}:")
print(f"  Ventas Total:   ${total_ventas:,.2f}")
print(f"  Gastos Total:   ${total_gastos:,.2f}")
print(f"  Ganancia Total: ${total_ganancia:,.2f}")
print(f"  Rentabilidad Promedio: {rentabilidad_promedio:.2f}%")

if not df.empty:
    mejor_mes = df.loc[df['Ventas_Total'].idxmax()]
    peor_mes = df.loc[df['Ventas_Total'].idxmin()]
    print(f"\n🏆 MEJOR MES (Ventas): {mejor_mes['Mes']} (${mejor_mes['Ventas_Total']:,.2f})")
    print(f"📉 PEOR MES (Ventas):  {peor_mes['Mes']} (${peor_mes['Ventas_Total']:,.2f})")
    if df['Rentabilidad'].max() > 0:
        mas_rentable = df.loc[df['Rentabilidad'].idxmax()]
        print(f"💰 MÁS RENTABLE: {mas_rentable['Mes']} ({mas_rentable['Rentabilidad']:.2f}%)")

# ============================================================
# TOP PROVEEDORES
# ============================================================
print("\n" + "="*70)
print("🏆 TOP 10 PROVEEDORES - TODOS LOS MESES")
print("="*70)

proveedores_totales = {}
for r in resultados:
    for prov, monto in r.get('Proveedores', {}).items():
        proveedores_totales[prov] = proveedores_totales.get(prov, 0) + monto

if proveedores_totales:
    top_general = sorted(proveedores_totales.items(), key=lambda x: x[1], reverse=True)[:10]
    for i, (prov, monto) in enumerate(top_general, 1):
        print(f"  {i:2}. {prov[:35]:35} ${monto:>12,.2f}")
else:
    print("  ⚠️ No se encontraron proveedores")

# ============================================================
# GRÁFICOS
# ============================================================
print("\n" + "="*70)
print("📊 GENERANDO GRÁFICOS")
print("="*70)

meses_pdf = df['Mes'].tolist()
meses_abv = []
for m in meses_pdf:
    partes = m.split()
    if len(partes) >= 2:
        mes_abv = partes[0][:3] + '-' + partes[1][-2:]
        meses_abv.append(mes_abv)
    else:
        meses_abv.append(m[:3])

ventas_total = df['Ventas_Total'].tolist()
gastos_total = df['Gastos_Total'].tolist()
rentabilidad = df['Rentabilidad'].tolist()

# Gráfico 1: Ventas vs Gastos
fig1, ax = plt.subplots(figsize=(12, 6))
x = np.arange(len(df))
width = 0.35
ax.bar(x - width/2, df['Ventas_Total'], width, label='Ventas', color='#2ecc71', alpha=0.8)
ax.bar(x + width/2, df['Gastos_Total'], width, label='Gastos', color='#e74c3c', alpha=0.8)
ax.set_xlabel('Mes', fontsize=12)
ax.set_ylabel('Monto', fontsize=12)
ax.set_title(f'Ventas vs Gastos por Mes - {AÑO_FILTRO}', fontsize=14, fontweight='bold')
ax.set_xticks(x)
ax.set_xticklabels(meses_abv, rotation=45)
ax.legend()
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

# Gráfico 2: Rentabilidad
fig2 = None
if df['Rentabilidad'].sum() > 0:
    fig2, ax = plt.subplots(figsize=(12, 6))
    colors_bar = ['#2ecc71' if x > 0 else '#e74c3c' for x in df['Rentabilidad']]
    bars = ax.bar(meses_abv, df['Rentabilidad'], color=colors_bar, edgecolor='black', alpha=0.8)
    ax.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax.set_xlabel('Mes', fontsize=12)
    ax.set_ylabel('Rentabilidad (%)', fontsize=12)
    ax.set_title(f'Rentabilidad por Mes - {AÑO_FILTRO}', fontsize=14, fontweight='bold')
    ax.set_xticklabels(meses_abv, rotation=45)
    ax.grid(True, alpha=0.3)
    for bar, val in zip(bars, df['Rentabilidad']):
        ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
                f'{val:.1f}%', ha='center', va='bottom', fontsize=9)
    plt.tight_layout()
    plt.show()

# Gráfico 3: Mapa de Calor
ventas_diarias = {}
for r in resultados:
    mes = r['Mes']
    for dia, monto in r.get('Ventas_Diarias', {}).items():
        if mes not in ventas_diarias:
            ventas_diarias[mes] = {}
        ventas_diarias[mes][dia] = monto

fig3 = None
if ventas_diarias:
    df_calor = pd.DataFrame(index=range(1, 32))
    for mes, datos in ventas_diarias.items():
        df_calor[mes] = pd.Series(datos)
    df_calor = df_calor.fillna(0)
    columnas_ordenadas = [m for m in df['Mes'].tolist() if m in df_calor.columns]
    if columnas_ordenadas:
        df_calor = df_calor[columnas_ordenadas]
    fig3, ax = plt.subplots(figsize=(14, 8))
    sns.heatmap(df_calor, cmap='YlOrRd', annot=True, fmt='.0f',
                cbar_kws={'label': 'Ventas ($)'}, linewidths=0.5, linecolor='white')
    plt.title(f'🔥 Mapa de Calor - Ventas por Día y Mes ({AÑO_FILTRO})', fontsize=14, fontweight='bold')
    plt.xlabel('Mes', fontsize=12)
    plt.ylabel('Día del Mes', fontsize=12)
    plt.tight_layout()
    plt.show()

# ============================================================
# FUNCIONES DE FORMATO
# ============================================================
def formato_cop(valor):
    if pd.isna(valor) or valor == 0:
        return "$0"
    return f"${valor:,.0f}".replace(",", ".")

def formato_porc(valor):
    if pd.isna(valor) or valor == 0:
        return "0%"
    return f"{valor:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".")

# ============================================================
# GENERAR INFORME PDF
# ============================================================
print("\n" + "="*70)
print("📄 GENERANDO INFORME PDF")
print("="*70)

nombre_pdf = f"Informe_King_Cholao_{AÑO_FILTRO}_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
doc = SimpleDocTemplate(nombre_pdf, pagesize=letter,
                        rightMargin=0.75*cm, leftMargin=0.75*cm,
                        topMargin=1*cm, bottomMargin=1*cm)

styles = getSampleStyleSheet()
style_title = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, alignment=TA_CENTER, spaceAfter=5)
style_subtitle = ParagraphStyle('SubTitle', parent=styles['Heading4'], fontSize=10, alignment=TA_CENTER, textColor=colors.grey, spaceAfter=15)
style_h2 = ParagraphStyle('H2', parent=styles['Heading2'], fontSize=14, spaceAfter=10)
style_cell = ParagraphStyle('Cell', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER)
style_cell_right = ParagraphStyle('CellRight', parent=styles['Normal'], fontSize=8, alignment=TA_RIGHT)
style_cell_left = ParagraphStyle('CellLeft', parent=styles['Normal'], fontSize=8, alignment=TA_LEFT)

story = []

story.append(Paragraph("KING CHOLAO", style_title))
story.append(Paragraph(f"INFORME FINANCIERO - {AÑO_FILTRO}", style_subtitle))
story.append(Spacer(1, 0.3*cm))

# KPI
kpi_data = [
    ["Ventas Totales", total_ventas, '#2E86C1'],
    ["Gastos Totales", total_gastos, '#E74C3C'],
    ["Ganancia Total", total_ganancia, '#28B463'],
    ["Rentabilidad Prom.", rentabilidad_promedio, '#F39C12']
]

kpi_table_data = []
for label, valor, color in kpi_data:
    texto = formato_porc(valor) if 'Rentabilidad' in label else formato_cop(valor)
    kpi_table_data.append([
        Paragraph(f'<para align="center" fontSize="10" textColor="white"><b>{label}</b></para>', 
                  ParagraphStyle('', parent=styles['Normal'], alignment=TA_CENTER)),
        Paragraph(f'<para align="center" fontSize="14" textColor="white"><b>{texto}</b></para>',
                  ParagraphStyle('', parent=styles['Normal'], alignment=TA_CENTER))
    ])

kpi_table = Table(kpi_table_data, colWidths=[2*inch, 2.5*inch])
for i, (_, _, color) in enumerate(kpi_data):
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, i), (1, i), color),
        ('ALIGN', (0, i), (1, i), 'CENTER'),
        ('VALIGN', (0, i), (1, i), 'MIDDLE'),
        ('TOPPADDING', (0, i), (1, i), 8),
        ('BOTTOMPADDING', (0, i), (1, i), 8),
    ]))
kpi_table.setStyle(TableStyle([
    ('GRID', (0,0), (-1,-1), 1, colors.white),
    ('BOX', (0,0), (-1,-1), 2, colors.black),
]))
story.append(kpi_table)
story.append(Spacer(1, 0.5*cm))

# Resumen
resumen = f"<b>Mejor Mes:</b> {mejor_mes['Mes']} ({formato_cop(mejor_mes['Ventas_Total'])}) | <b>Peor Mes:</b> {peor_mes['Mes']} ({formato_cop(peor_mes['Ventas_Total'])})"
if 'mas_rentable' in locals():
    resumen += f" | <b>Más Rentable:</b> {mas_rentable['Mes']} ({formato_porc(mas_rentable['Rentabilidad'])})"
story.append(Paragraph(resumen, ParagraphStyle('Resumen', parent=styles['Normal'], fontSize=9, alignment=TA_CENTER, textColor=colors.darkgrey)))
story.append(Spacer(1, 0.5*cm))

# Insertar gráficos
def fig_to_image(fig, width=6*inch, height=3.5*inch):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=120, bbox_inches='tight')
    buf.seek(0)
    return Image(buf, width=width, height=height)

story.append(Paragraph("Evolución Mensual - Ventas vs Gastos", style_h2))
story.append(fig_to_image(fig1, width=6*inch, height=3*inch))
story.append(Spacer(1, 0.3*cm))

if fig2 is not None:
    story.append(Paragraph("Rentabilidad por Mes", style_h2))
    story.append(fig_to_image(fig2, width=6*inch, height=3*inch))
    story.append(Spacer(1, 0.3*cm))

if fig3 is not None:
    story.append(Paragraph("Mapa de Calor - Ventas Diarias", style_h2))
    story.append(fig_to_image(fig3, width=6*inch, height=3.5*inch))
    story.append(Spacer(1, 0.3*cm))

story.append(PageBreak())

# Tabla Ventas
story.append(Paragraph("Ventas por Mes (Efectivo vs Tarjeta)", style_h2))
ventas_tabla = [[Paragraph("<b>Mes</b>", style_cell), 
                 Paragraph("<b>Efectivo</b>", style_cell_right),
                 Paragraph("<b>Tarjeta</b>", style_cell_right),
                 Paragraph("<b>Total</b>", style_cell_right)]]

for i, m in enumerate(meses_abv):
    ventas_tabla.append([
        Paragraph(m, style_cell),
        Paragraph(formato_cop(df['Ventas_Efectivo'].iloc[i]), style_cell_right),
        Paragraph(formato_cop(df['Ventas_Tarjeta'].iloc[i]), style_cell_right),
        Paragraph(formato_cop(ventas_total[i]), style_cell_right)
    ])

ventas_tabla.append([
    Paragraph("<b>TOTAL</b>", style_cell),
    Paragraph(formato_cop(df['Ventas_Efectivo'].sum()), style_cell_right),
    Paragraph(formato_cop(df['Ventas_Tarjeta'].sum()), style_cell_right),
    Paragraph(formato_cop(total_ventas), style_cell_right)
])

t_ventas = Table(ventas_tabla, colWidths=[1.2*inch, 1.6*inch, 1.6*inch, 1.8*inch])
t_ventas.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1B4F72')), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
    ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('FONTSIZE', (0,0), (-1,0), 10),
    ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.whitesmoke, colors.HexColor('#E8F8F5')]),
    ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#D5D8DC')), ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
    ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BOX', (0,0), (-1,-1), 1.5, colors.black),
]))
story.append(t_ventas)
story.append(Spacer(1, 0.5*cm))

# Tabla Gastos
story.append(Paragraph("Gastos Desglosados por Mes", style_h2))
gastos_tabla = [[Paragraph("<b>Mes</b>", style_cell),
                 Paragraph("<b>Compras</b>", style_cell_right),
                 Paragraph("<b>Personal</b>", style_cell_right),
                 Paragraph("<b>Servicios</b>", style_cell_right),
                 Paragraph("<b>Otros</b>", style_cell_right),
                 Paragraph("<b>Total</b>", style_cell_right)]]

for i, m in enumerate(meses_abv):
    gastos_tabla.append([
        Paragraph(m, style_cell),
        Paragraph(formato_cop(df['Gastos_Compras'].iloc[i]), style_cell_right),
        Paragraph(formato_cop(df['Gastos_Personal'].iloc[i]), style_cell_right),
        Paragraph(formato_cop(df['Gastos_Servicios'].iloc[i]), style_cell_right),
        Paragraph(formato_cop(df['Gastos_Otros'].iloc[i]), style_cell_right),
        Paragraph(formato_cop(gastos_total[i]), style_cell_right)
    ])

gastos_tabla.append([
    Paragraph("<b>TOTAL</b>", style_cell),
    Paragraph(formato_cop(df['Gastos_Compras'].sum()), style_cell_right),
    Paragraph(formato_cop(df['Gastos_Personal'].sum()), style_cell_right),
    Paragraph(formato_cop(df['Gastos_Servicios'].sum()), style_cell_right),
    Paragraph(formato_cop(df['Gastos_Otros'].sum()), style_cell_right),
    Paragraph(formato_cop(total_gastos), style_cell_right)
])

t_gastos = Table(gastos_tabla, colWidths=[1.0*inch, 1.2*inch, 1.2*inch, 1.2*inch, 1.0*inch, 1.2*inch])
t_gastos.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#641E16')), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
    ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('FONTSIZE', (0,0), (-1,0), 9),
    ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.whitesmoke, colors.HexColor('#FDEDEC')]),
    ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#D5D8DC')), ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
    ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BOX', (0,0), (-1,-1), 1.5, colors.black),
]))
story.append(t_gastos)
story.append(PageBreak())

# Tabla Top 10 Proveedores
story.append(Paragraph("Top 10 Proveedores (Acumulado)", style_h2))
prov_tabla = [[Paragraph("<b>#</b>", style_cell), 
               Paragraph("<b>Proveedor</b>", style_cell_left),
               Paragraph("<b>Monto Total</b>", style_cell_right)]]

if proveedores_totales:
    top_prov = sorted(proveedores_totales.items(), key=lambda x: x[1], reverse=True)[:10]
    for idx, (nombre, monto) in enumerate(top_prov, 1):
        prov_tabla.append([
            Paragraph(str(idx), style_cell),
            Paragraph(nombre, style_cell_left),
            Paragraph(formato_cop(monto), style_cell_right)
        ])
    prov_tabla.append([
        Paragraph("<b>TOTAL</b>", style_cell),
        Paragraph("", style_cell),
        Paragraph(formato_cop(sum([m for _, m in top_prov])), style_cell_right)
    ])
else:
    prov_tabla.append([
        Paragraph("", style_cell),
        Paragraph("No se encontraron proveedores", style_cell_left),
        Paragraph("", style_cell_right)
    ])

t_prov = Table(prov_tabla, colWidths=[0.6*inch, 3.0*inch, 1.6*inch])
t_prov.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E8449')), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
    ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('FONTSIZE', (0,0), (-1,0), 10),
    ('ROWBACKGROUNDS', (0,1), (-1,-2), [colors.whitesmoke, colors.HexColor('#E8F8E8')]),
    ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor('#D5D8DC')), ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
    ('GRID', (0,0), (-1,-1), 0.5, colors.grey), ('BOX', (0,0), (-1,-1), 1.5, colors.black),
    ('ALIGN', (2,0), (2,-1), 'RIGHT'),
]))
story.append(t_prov)

# Pie de página
story.append(Spacer(1, 1*cm))
story.append(Paragraph(f"Informe generado automáticamente desde GitHub el {datetime.now().strftime('%Y-%m-%d %H:%M')}", 
                       ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.grey)))

# Construir PDF
doc.build(story)
print(f"✅ PDF generado: {nombre_pdf}")

# Descargar en Colab
from google.colab import files
files.download(nombre_pdf)
print("✅ PDF descargado en tu computadora.")

print("\n" + "="*70)
print("✅ ANÁLISIS COMPLETADO (PDF MEJORADO)")
print("="*70)
