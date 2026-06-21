import pandas as pd
import matplotlib.pyplot as plt


# --- Leitura do CSV ---
df = pd.read_csv("StatsVanderson.csv")

# Ajusta data/hora
df["DATA DA ENTRADA (DD-MM-YY HH:MM)"] = pd.to_datetime(df["DATA DA ENTRADA (DD-MM-YY HH:MM)"], format="%d-%m-%y %H:%M")

# Normaliza colunas
df["RESULTADO"] = df["RESULTADO"].str.strip().str.lower()
df["OBSERVAÇÃO"] = df["OBSERVAÇÃO"].fillna("").str.lower()

# 1. Porcentagem de operações ganhadoras
win_rate = (df["RESULTADO"] == "gain").mean() * 100


# 2. Maior sequência ganhadora
def longest_streak(series, target):
    max_streak = streak = 0
    for val in series:
        if val == target:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 0
    return max_streak


longest_win_streak = longest_streak(df["RESULTADO"], "gain")
longest_loss_streak = longest_streak(df["RESULTADO"], "loss")

# --- Performance por horário (Win Rate) ---
df["hora"] = df["DATA DA ENTRADA (DD-MM-YY HH:MM)"].dt.hour
df["turno"] = df["hora"].apply(lambda h: "manhã" if h < 12 else "tarde")

# Win Rate por turno (% de gains)
win_rate_turno = df.groupby("turno")["RESULTADO"].apply(lambda x: (x == "gain").mean() * 100)

melhor_turno = win_rate_turno.idxmax()
pior_turno = win_rate_turno.idxmin()

# --- Performance por perfil de mercado (Win Rate) ---
df["perfil"] = df["OBSERVAÇÃO"].apply(lambda obs: "tendência" if "tendencia" in obs else "lateralizado")

win_rate_perfil = df.groupby("perfil")["RESULTADO"].apply(lambda x: (x == "gain").mean() * 100)

# --- Gráficos ---
plt.style.use("seaborn-v0_8")  # estilo mais agradável

plt.figure(figsize=(14, 8))

# Gráfico 1 - Evolução financeira (índice das operações no eixo X)
plt.subplot(2, 2, 1)
df["financeiro_acumulado"] = df["FINANCEIRO"].cumsum()
x = range(1, len(df) + 1)
y = df["financeiro_acumulado"]

plt.plot(
    x,
    y,
    marker="o",
    linestyle="-",
    color="royalblue",
    linewidth=2,
    markersize=6,
    alpha=0.9,
)

# Preenche abaixo da curva com verde/vermelho
plt.fill_between(x, y, 0, where=(y >= 0), interpolate=True, color="mediumseagreen", alpha=0.3)
plt.fill_between(x, y, 0, where=(y < 0), interpolate=True, color="tomato", alpha=0.3)

# Marca o valor final no último ponto
final_x = x[-1]
final_y = y.iloc[-1]
plt.text(final_x, final_y, f"{final_y:.2f}", fontsize=10, fontweight="bold", color="black", ha="left", va="bottom")

plt.title("Evolução Financeira da Estratégia", fontsize=12, fontweight="bold")
plt.xlabel("Número da Operação")
plt.ylabel("Financeiro Acumulado")
plt.grid(alpha=0.3)

# Gráfico 2 - Pizza win/loss
plt.subplot(2, 2, 2)
colors = ["mediumseagreen", "tomato"]
df["RESULTADO"].value_counts().plot.pie(autopct="%1.1f%%", startangle=90, colors=colors, labels=["Gain", "Loss"])
plt.title("Distribuição de Resultados", fontsize=12, fontweight="bold")

# Gráfico 3 - Sequências
plt.subplot(2, 2, 3)
seq_values = [longest_win_streak, longest_loss_streak]
seq_colors = ["mediumseagreen" if v >= 0 else "tomato" for v in seq_values]

plt.bar(
    ["Maior sequência de Gains", "Maior sequência de Losses"],
    seq_values,
    color=seq_colors,
    alpha=0.8,
)
plt.title("Maiores Sequências", fontsize=12, fontweight="bold")
plt.ylabel("Número de Operações")
plt.grid(axis="y", alpha=0.3)

# --- Gráfico 4 - Win Rate por Turno e Perfil ---
plt.subplot(2, 2, 4)

bar_width = 0.35

turno_positions = range(len(win_rate_turno))
perfil_positions = range(len(win_rate_turno), len(win_rate_turno) + len(win_rate_perfil))

# Verde se win rate >= 50%, vermelho se menor
turno_colors = ["mediumseagreen" if v >= 50 else "tomato" for v in win_rate_turno.values]
perfil_colors = ["darkorange" if v >= 50 else "tomato" for v in win_rate_perfil.values]

# Plot turnos
plt.bar(
    turno_positions,
    win_rate_turno.values,
    width=bar_width,
    label="Turnos",
    color=turno_colors,
    alpha=0.8,
)

# Plot perfis
plt.bar(
    perfil_positions,
    win_rate_perfil.values,
    width=bar_width,
    label="Perfis de Mercado",
    color=perfil_colors,
    alpha=0.8,
)

plt.axhline(50, color="gray", linewidth=1, linestyle="--")  # linha de referência 50%
xticks_labels = list(win_rate_turno.index) + list(win_rate_perfil.index)
plt.xticks(list(turno_positions) + list(perfil_positions), xticks_labels, rotation=0)

plt.title("Win Rate por Turno e Perfil de Mercado", fontsize=12, fontweight="bold")
plt.ylabel("Win Rate (%)")
plt.grid(axis="y", alpha=0.3)
plt.legend()

plt.tight_layout()
plt.show()

# --- Impressão das estatísticas ---
print(f"1. Win Rate: {win_rate:.2f}%")
print(f"2. Maior sequência ganhadora: {longest_win_streak}")
print(f"3. Maior sequência perdedora: {longest_loss_streak}")
print(f"4. Melhor faixa de horário: {melhor_turno}")
print(f"5. Pior faixa de horário: {pior_turno}")
print(f"6. Performance por perfil de mercado:\n{win_rate_perfil.to_string()}")
