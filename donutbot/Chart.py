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
            ax = plt.gca()
            max_user = next(iter(self.logic.get_top()))
            max_projection = int(self.logic.get_stats_by_display_name(max_user).projection * 1.25)

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
                        line_kws={"ls": "--", "lw": 1.5, "alpha": 0.5},
                        color=color, ax=ax
                        )

                    regression = linregress(user_data['time_numeric'], user_data['cumulative_score'])
                    final_y = regression.slope * end_date + regression.intercept # type: ignore

                    if len(list(filter(lambda area: final_y > area[0] and final_y < area[1], used_label_areas))) > 0:
                        final_y += 10

                    used_label_areas.append((final_y - 5, final_y + 5))

                    ax.text(
                        end_date + 2,
                        final_y,
                        user,
                        color=color,
                        va='center',
                        ha='left',
                        fontsize=9,
                        fontweight='bold'
                    )

        else:
            plt.figure(figsize=(12, 7))
            ax = plt.gca()

            daily_data = data.sort_values(['username', 'time']).groupby(
                ['username', 'time_numeric']
            ).last().reset_index()

            usernames = sorted(daily_data['username'].unique())
            palette = sns.color_palette("husl", len(usernames))
            color_map = dict(zip(usernames, palette))

            used_label_areas = []
            for user in usernames:
                user_plot_data = daily_data[daily_data['username'] == user]
                color = color_map[user]

                ax.plot(
                    user_plot_data['time_numeric'],
                    user_plot_data['cumulative_score'],
                    marker='o',
                    markersize=4,
                    linewidth=2,
                    color=color,
                    label=user,
                    linestyle='-'
                )

                last_row = user_plot_data.iloc[-1]
                label_x = last_row['time_numeric'] + 0.3
                label_y = last_row['cumulative_score']

                if (label_x, label_y) in used_label_areas:
                    label_y += 1

                ax.text(
                    label_x,
                    label_y,
                    user,
                    color=color,
                    fontweight='bold',
                    va='center',
                    ha='left',
                    fontsize=9
                )

                used_label_areas.append((label_x, label_y))

            ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
            ax.xaxis.set_major_locator(mdates.AutoDateLocator())

            current_xlim = ax.get_xlim()
            ax.set_xlim(current_xlim[0], current_xlim[1] + (current_xlim[1] - current_xlim[0]) * 0.15)

        plt.xticks(rotation=45)
        plt.xlabel("Date")
        plt.ylabel("Score")

        today_ordinal = datetime.now().toordinal()
        plt.axvline(today_ordinal, color='black', linestyle=':', alpha=0.5)
        plt.text(today_ordinal, plt.ylim()[1], ' TODAY', rotation=0, va='bottom', fontweight='bold')
        plt.title("DONUTS DONUTS DONUTS")
        plt.grid(True, alpha=0.2)

        plt.savefig(self.CHART_FILE, dpi=300, bbox_inches='tight')
