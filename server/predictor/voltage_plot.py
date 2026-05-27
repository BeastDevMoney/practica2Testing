import sys
import os
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import timedelta

def main():
    if len(sys.argv) < 4:
        print("Uso: voltage_plot.py <csv_path> <target_field> <margin_minutes>")
        sys.exit(1)

    csv_path = sys.argv[1]
    target_field = sys.argv[2]
    margin_minutes = int(sys.argv[3])

    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    print(root_path)

    if root_path not in sys.path:
        sys.path.insert(0, root_path)

    os.chdir(root_path)

    from server.integration.csv_reader import CSVReader
    from server.predictor.scheduler import Scheduler
    from server.predictor.incidence_predictor import Incidence_Predictor

    import tempfile
    from datetime import datetime, timezone
    from server.business_logic.incidence_service import PREDICTION_CACHE

    print(f"Cargando '{csv_path}'...")
    measurements = CSVReader().readCSV(csv_path)
    print(f"  {len(measurements)} medidas.")

    scheduler = Scheduler()
    predictor = Incidence_Predictor(scheduler, target_field=target_field)

    cache_file = f"{PREDICTION_CACHE}_{target_field}.npz"
    if os.path.exists(cache_file):
        print(f"Cargando predicciones desde cache ({cache_file})...")
        data = np.load(cache_file, allow_pickle=False)
        times = [datetime.fromtimestamp(ts) for ts in data["times_epoch"]]
        y_real = data["y_real"]
        y_pred = data["y_pred"]
    else:
        print("Cache no encontrado. Entrenando modelo de regresión...")
        times, y_real, y_pred = predictor.predict_voltage(measurements, target_field)
        if not len(times):
            print("No se pudo entrenar el modelo.")
            sys.exit(1)

    from sklearn.metrics import mean_absolute_error, mean_squared_error
    mae = mean_absolute_error(y_real, y_pred)
    rmse = float(np.sqrt(mean_squared_error(y_real, y_pred)))
    print(f"MAE={mae:.2f} mV  RMSE={rmse:.2f} mV")

    incidences = predictor.analyzeMeasurements(measurements)
    print(f"  {len(incidences)} incidencias detectadas.")

    from server.domain.incidence import IncidenceType

    fj_incidences = [i for i in incidences if i.tipoIncidencia == IncidenceType.FREQUENCY_JUMP]
    if fj_incidences:
        print(f"Generando plot FREQUENCY_JUMP...")
        _plot(times, y_real, y_pred, fj_incidences, target_field, margin_minutes, measurements, inc_type_filter=IncidenceType.FREQUENCY_JUMP)
    else:
        print("No hay incidencias FREQUENCY_JUMP en el test set.")

    ab_incidences = [i for i in incidences if i.tipoIncidencia == IncidenceType.ABSENCE]
    if ab_incidences:
        print(f"Generando plot ABSENCE...")
        _plot(times, y_real, y_pred, ab_incidences, target_field, margin_minutes, measurements, inc_type_filter=IncidenceType.ABSENCE)
    else:
        print("No hay incidencias ABSENCE en el test set.")


def _find_incidence(times_arr, incidences):
    test_start = times_arr[0]
    test_end = times_arr[-1]

    in_test = [i for i in incidences if test_start <= i.start <= test_end]
    if in_test:
        return in_test[0]

    if incidences:
        return min(incidences, key=lambda i: abs((i.start - test_end).total_seconds()))

    return None


def _plot(times, y_real, y_pred, incidences, target_field, margin_minutes, measurements=None, inc_type_filter=None):
    label_map = {
        "vr1_a": "Receptor 1 - canal A",
        "vr1_b": "Receptor 1 - canal B",
        "vr2_a": "Receptor 2 - canal A",
        "vr2_b": "Receptor 2 - canal B",
    }
    label = label_map.get(target_field, target_field)

    times_arr = np.array(times)
    errors_all = np.abs(y_real - y_pred)

    # --- Arrays del dataset completo para la zona post-incidencia ---
    if measurements is not None:
        all_ms = sorted(measurements, key=lambda m: m.time)
        all_t = np.array([m.time for m in all_ms])
        all_v = np.array([
            float(getattr(m, target_field)) if getattr(m, target_field) is not None
            else np.nan
            for m in all_ms
        ], dtype=float)
    else:
        all_t = times_arr
        all_v = y_real

    # --- Centro de la ventana ---
    target_inc = _find_incidence(times_arr, incidences)

    type_label = inc_type_filter.name if inc_type_filter is not None else "INCIDENCIA"

    if target_inc is None:
        peak_idx = int(np.argmax(errors_all))
        center = times_arr[peak_idx]
        inc_start_dt = None
        inc_end_dt = None
        title_inc = f"ventana de mayor error (sin {type_label} en test set)"
        print(f"Sin {type_label} en test set; mostrando ventana de mayor error.")
    else:
        center = target_inc.start
        inc_start_dt = target_inc.start
        inc_end_dt = target_inc.end
        title_inc = (
            f"{target_inc.tipoIncidencia.name}  "
            f"{target_inc.start:%Y-%m-%d %H:%M} → {target_inc.end:%Y-%m-%d %H:%M}"
        )

    lo = center - timedelta(minutes=margin_minutes)
    hi = center + timedelta(minutes=margin_minutes)

    mask_test = (times_arr >= lo) & (times_arr <= hi)
    tw_test = times_arr[mask_test]
    yr_w = y_real[mask_test]
    yp_w = y_pred[mask_test]
    errors = np.abs(yr_w - yp_w)

    mask_all = (all_t >= lo) & (all_t <= hi)
    tw_all = all_t[mask_all]
    vr_all = all_v[mask_all]

    tw_display = tw_all if len(tw_all) > 0 else tw_test
    date_start = tw_display[0].strftime("%Y-%m-%d")
    date_end = tw_display[-1].strftime("%Y-%m-%d")
    date_str = date_start if date_start == date_end else f"{date_start} / {date_end}"

    fig, axes = plt.subplots(3, 1, figsize=(13, 9), sharex=False, gridspec_kw={"height_ratios": [3, 1, 0.6]})

    # ---- Panel superior: real vs predicho ----
    ax = axes[0]

    ax.plot(tw_all, vr_all, label="Real", color="royalblue", linewidth=1.6)

    if len(tw_test) > 0:
        ax.plot(tw_test, yp_w, label="Esperado (modelo)", color="darkorange", linewidth=1.6, linestyle="--")
        ax.fill_between(tw_test, yr_w, yp_w, alpha=0.18, color="gray", label="Error")

    if inc_start_dt is not None:
        from server.domain.incidence import IncidenceType
        if target_inc.tipoIncidencia == IncidenceType.ABSENCE:
            span_lo = max(inc_start_dt, lo)
            span_hi = min(inc_end_dt, hi)
            if span_lo < span_hi:
                ax.axvspan(span_lo, span_hi, color="red", alpha=0.12, label=f"Incidencia ({target_inc.tipoIncidencia.name})")
        ax.axvline(inc_start_dt, color="red", linewidth=1.4, linestyle=":", label=f"Inicio incidencia {inc_start_dt:%H:%M}")

        if len(tw_all) > 0:
            idx_closest = int(np.argmin(np.abs(tw_all - inc_start_dt)))
            ax.scatter(tw_all[idx_closest], vr_all[idx_closest], color="red", zorder=6, s=100, label=f"Detección ({inc_start_dt:%H:%M})")
            ax.annotate(
                f"Incidencia\n{inc_start_dt:%H:%M}",
                xy=(tw_all[idx_closest], vr_all[idx_closest]),
                xytext=(10, -22), textcoords="offset points",
                fontsize=8, color="red",
                arrowprops=dict(arrowstyle="->", color="red", lw=1.0)
            )

    # Errores anotados (solo donde hay predicción)
    for t_pt, yr_v, yp_v in zip(tw_test, yr_w, yp_w):
        ax.annotate(f"{abs(yp_v - yr_v):.1f}", xy=(t_pt, max(yr_v, yp_v)), xytext=(0, 5), textcoords="offset points", fontsize=7, ha="center", color="dimgray")

    ax.set_title(
        f"{label}  -  {date_str}\n"
        f"{title_inc}  |  ventana ±{margin_minutes} min"
    )
    ax.set_ylabel("Voltaje (mV)")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.35)

    # ---- Panel inferior: error absoluto por minuto ----
    bar_width = timedelta(seconds=40)
    if len(tw_test) > 0:
        axes[1].bar(tw_test, errors, width=bar_width, color="salmon", alpha=0.8)
        axes[1].axhline(errors.mean(), color="darkorange", linewidth=1.2, linestyle="--", label=f"MAE zona = {errors.mean():.1f} mV")
    axes[1].set_ylabel("|Error| (mV)")
    axes[1].legend(fontsize=8)
    axes[1].grid(True, alpha=0.35, axis="y")

    # ---- Panel 3: estado de la vía ----
    ax3 = axes[2]

    if measurements is not None:
        all_ms_sorted = sorted(measurements, key=lambda m: m.time)
        st_times = np.array([m.time for m in all_ms_sorted if lo <= m.time <= hi and m.status is not None])
        st_vals = np.array([int(m.status) for m in all_ms_sorted if lo <= m.time <= hi and m.status is not None])
    else:
        st_times = tw_all
        st_vals = np.ones(len(tw_all), dtype=int)

    if len(st_times) > 0:
        for i in range(len(st_times) - 1):
            color = "#43d9a2" if st_vals[i] == 1 else "#f05c6e"
            ax3.fill_between([st_times[i], st_times[i+1]], 0, 1, color=color, alpha=0.5, step="post")
            ax3.step([st_times[i], st_times[i+1]], [st_vals[i], st_vals[i]], color=color, linewidth=1.5, where="post")

        color = "#43d9a2" if st_vals[-1] == 1 else "#f05c6e"
        ax3.fill_between([st_times[-1], hi], 0, 1, color=color, alpha=0.5, step="post")

    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor="#43d9a2", alpha=0.6, label="Vacía (1)"),
        Patch(facecolor="#f05c6e", alpha=0.6, label="Ocupada (0)"),
    ]
    ax3.legend(handles=legend_elements, loc="upper right", fontsize=8)
    ax3.set_ylabel("Vía", fontsize=9)
    ax3.set_xlabel("Hora")
    ax3.set_ylim(-0.05, 1.2)
    ax3.set_yticks([0, 1])
    ax3.set_yticklabels(["Ocup.", "Vacía"], fontsize=8)
    ax3.grid(True, alpha=0.2, axis="x")

    for ax_ in axes:
        ax_.set_xlim(lo, hi)
        ax_.xaxis.set_major_locator(mdates.MinuteLocator(interval=1))
        ax_.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        ax_.tick_params(axis="x", rotation=45)

    fig.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()