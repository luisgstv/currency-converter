import customtkinter as ctk
import requests
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
from dateutil.relativedelta import relativedelta
import threading

# Getting the API_KEY
from key import API_KEY

class App(ctk.CTk):
    def __init__(self):
        # App basic informations
        super().__init__(fg_color='#0f0f0f')
        self.title('Currency Converter')
        self.geometry('900x600+0+0')
        
        # Generating the currencies
        self.currencies, self.currencies_names = self.get_currencies()

        # Variables for conversion
        self.from_var = ctk.StringVar(value='US Dollar')
        self.to_var = ctk.StringVar(value='Brazilian Real')
        self.amount_var = ctk.StringVar(value='1')
        self.output_var = ctk.StringVar()

        # Conversion widgets
        self.currency_selector_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.from_button = ctk.CTkComboBox(self.currency_selector_frame, values=self.currencies_names, variable=self.from_var)
        self.to_button = ctk.CTkComboBox(self.currency_selector_frame, values=self.currencies_names, variable=self.to_var)

        self.amount_entry = ctk.CTkEntry(self, textvariable=self.amount_var)
        self.convert_button = ctk.CTkButton(self, text='Convert', command=lambda: threading.Thread(target=self.convert).start(), font=('Century Gothic', 18))
        self.output_value = ctk.CTkLabel(self, textvariable=self.output_var, font=('Century Gothic', 18))

        # Conversion widgets layout
        self.currency_selector_frame.pack(pady=5)
        self.from_button.pack(side='left', expand=True, padx=15)
        self.to_button.pack(side='left', expand=True, padx=15)

        self.amount_entry.pack(pady=5)
        self.convert_button.pack(pady=5)
        self.output_value.pack(pady=5)

        #  Graphic widgets
        self.graph_frame = ctk.CTkFrame(self, fg_color='transparent')
        self.graph_label = ctk.CTkLabel(self.graph_frame, text='Last 3 Months', font=('Century Gothic', 18))

        # Creating the graphic
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)

        # Graphic widgets layout
        self.graph_frame.pack(pady=5, expand=True, fill='both')
        self.graph_label.pack(pady=5)
        self.canvas.get_tk_widget().pack(expand=True, fill='both')

        # Graphic colors
        self.fig.patch.set_facecolor('#0f0f0f')
        self.ax.set_facecolor('#0f0f0f')

        # Hiding graphic axes
        self.ax.xaxis.set_visible(False)
        self.ax.yaxis.set_visible(False)
        
        # Creating the hover event
        self.canvas.mpl_connect("motion_notify_event", self.hover)

        # Initializing the initial conversion and the graphic
        self.convert()

    def get_currencies(self):
        # Do a request in the currencies endpoint
        currencies_url = f'https://api.currencybeacon.com/v1/currencies?api_key={API_KEY}'
        currencies_request = requests.get(currencies_url).json()['response']

        # Create a dictionary with the currencies' names, it's codes and symbols, and a list with each currency name
        currencies = {}
        currencies_names = []
        for currency in currencies_request:
            name = currency['name']
            code = currency['short_code']
            symbol = currency['symbol']
            symbol_first = currency['symbol_first']
            currencies[name] = {'code': code, 'symbol': symbol, 'symbol_first': symbol_first}
            currencies_names.append(name)
        return currencies, currencies_names

    def convert(self):
        # Get the currencies and it's informations, and the value to convert
        self.from_value = self.currencies[self.from_var.get()]['code']
        self.to_value = self.currencies[self.to_var.get()]['code']
        self.symbol = self.currencies[self.to_var.get()]['symbol']
        self.symbol_first = self.currencies[self.to_var.get()]['symbol_first']
        self.amount_value = self.amount_var.get()

        # Try to convert, if there's an incorrect value show an error in the output
        try:
            # Allows the use of commas
            if ',' in self.amount_value:
                self.amount_value = self.amount_value.replace(',', '.')

            # Do a request in the convert endpoint
            conversion_url = f'https://api.currencybeacon.com/v1/convert?api_key={API_KEY}&from={self.from_value}&to={self.to_value}&amount={self.amount_value}'
            conversion_request = requests.get(conversion_url).json()
            value = conversion_request['value']

            # Show the conversion in the output, with the symbol in it's correct position
            if self.symbol_first:
                self.output_var.set(f'{self.symbol} {value:.2f}')
            else:
                self.output_var.set(f'{value:.2f} {self.symbol}')

            # Initialize the graphic
            self.plot_graph(self.from_value, self.to_value)
        except:
            self.output_var.set('ERROR: invalid currency or number.')

    def plot_graph(self, from_value, to_value):
        # Getting the period
        self.end_date = datetime.now()
        self.start_date = self.end_date - relativedelta(months=3)

        # Do a request in the timeseries endpoint
        time_series_url = f"https://api.currencybeacon.com/v1/timeseries?api_key={API_KEY}&base={from_value}&start_date={self.start_date.strftime('%Y-%m-%d')}&end_date={self.end_date.strftime('%Y-%m-%d')}&symbols={to_value}"
        time_series_request = requests.get(time_series_url).json()
        dates = time_series_request['response']

        # Create a list with the formated dates and it's respective values
        date_list = []
        value_list = []
        for date, value in dates.items():
            date_list.append(datetime.strptime(date, '%Y-%m-%d').strftime('%m-%d-%Y'))
            value_list.append(value[to_value])
        
        # Cleaning the graphic and plotting a new one
        self.ax.clear()
        self.line, = self.ax.plot(date_list, value_list, marker='.', linestyle='-', color='white')

        # Creating the annotation
        self.annotation = self.ax.annotate(text="", xy=(0,0), xytext=(-80,25),
            textcoords="offset points",
            bbox={'boxstyle': 'round', 'fc': 'gray'},
            arrowprops={'arrowstyle': '->'}
        )
        self.annotation.set_visible(False)

        # Updating the graphic
        self.canvas.draw()

    def hover(self, event):
        # Checks if the mouse is over a line
        visible = self.annotation.get_visible()
        if event.inaxes == self.ax:
            contains, annotation_index = self.line.contains(event)
            if contains:
                # Define the annotation's x and y as the line marker x and y
                x, y = self.line.get_data()
                index = annotation_index['ind'][0]
                self.annotation.xy = (x[index], y[index])

                # Define the annotation's text with the date and it value
                text = f'Date: {x[index]}, Value: {y[index]:.3f}'
                self.annotation.set_text(text)

                # Turns the annotation visible
                self.annotation.set_visible(True)
                self.canvas.draw_idle()
            else:
                # Turns the annotation invisible
                if visible:
                    self.annotation.set_visible(False)
                    self.canvas.draw_idle()

# Runs the app
if __name__ == '__main__':
    app = App()
    app.mainloop()