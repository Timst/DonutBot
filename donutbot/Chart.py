from datetime import datetime

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from scipy.stats import linregress

from Data import Data
from Logic import Logic


class Chart:
    CHART_FILE = "/tmp/donut_chart.png"

    data: Data

    def __init__(self, data: Data, logic: Logic) -> None:
        self.data = data
        self.logic = logic

    def get_score_over_time(self) -> pd.DataFrame:
        df = self.data.get_dataframe()
        df['time'] = pd.to_datetime(df['time'], format="mixed")

        df['point_value'] = df.apply(
            lambda x: x['number'] if x['operation'] == 'add' else -x['number'],
            axis=1
        )

        df = df.sort_values(by=['username', 'time'])

        df['cumulative_score'] = df.groupby('username')['point_value'].cumsum()

        df['time_numeric'] = df['time'].map(pd.Timestamp.toordinal)

        return df

    def get_chart(self, project: bool):
        start_date = datetime(datetime.now().year, 1, 1).toordinal()
        end_date = datetime(datetime.now().year, 11, 30).toordinal()
        data = self.get_score_over_time()

        if project:
            plt.figure(figsize=(12, 7))
            max_user = next(iter(self.logic.get_top()))
            max_projection = int(self.logic.get_stats_by_display_name(max_user).projection * 1.25)

            ax = plt.gca()
            ax.set_xlim(start_date, end_date)
            ax.set_ylim(0, max_projection)
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
            ax.xaxis.set_major_locator(mdates.MonthLocator())

            colors = sns.color_palette("husl", len(data['username'].unique()))

            used_label_areas = []
            for i, user in enumerate(data['username'].unique()):
                user_data = data[data['username'] == user].sort_values('time_numeric')
                color = colors[i]

                sns.lineplot(
                    data=user_data, x="time_numeric", y="cumulative_score",
                    lw=2, color=color, label=user, ax=ax
                )

                if len(user_data) > 2:
                    sns.regplot(
                        data=user_data, x="time_numeric", y="cumulative_score",
                        truncate=False, ci=None, scatter=False,
                        line_kws={"ls": "--", "lw": 1, "alpha": 0.5},
                        color=color, ax=ax
                        )

                    regression = linregress(user_data['time_numeric'], user_data['cumulative_score'])
                    final_y = regression.slope * end_date + regression.intercept # type: ignore

                    if len(list(filter(lambda area: final_y > area[0] and final_y < area[1], used_label_areas))) > 0:
                        final_y += 6

                    used_label_areas.append((final_y - 5, final_y + 5))

                    plt.text(
                        end_date + 2, final_y, user,
                        color=color, va='center', ha='left', fontsize=9
                    )

        else:
            plt.figure(figsize=(12, 7))

            sns.lineplot(
                data=data,
                x="time_numeric",
                y="cumulative_score",
                hue="username",
                linewidth=2,
                marker='o',
                markersize=4,
                errorbar=('ci', False),
                palette="husl"
            )

            ax = plt.gca()
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())

        plt.xticks(rotation=45)
        plt.xlabel("Date")
        plt.ylabel("Score")

        today_ordinal = datetime.now().toordinal()
        plt.axvline(today_ordinal, color='black', linestyle=':', alpha=0.5)
        plt.text(today_ordinal, plt.ylim()[1], ' TODAY', rotation=0, va='bottom', fontweight='bold')
        plt.title("DONUTS DONUTS DONUTS")
        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.grid(True, alpha=0.2)

        legend = ax.get_legend()
        if project and legend:
            legend.remove()

        plt.savefig(self.CHART_FILE, dpi=300, bbox_inches='tight')
