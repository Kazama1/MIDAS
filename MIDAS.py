from kivy.config import Config
Config.set('graphics', 'multisamples', '0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from babel.numbers import format_currency
import requests

class CryptoConverterApp(App):
    def build(self):
        self.lista_criptos = self.obter_lista_criptos()
        self.moedas_fiat = ['USD', 'BRL']  # Lista de moedas fiduciárias suportadas

        layout = BoxLayout(orientation='vertical', padding=10)

        self.search_input = TextInput(hint_text='Digite o nome da criptomoeda', multiline=False)
        self.search_input.bind(on_text_validate=self.atualizar_lista_criptos)
        layout.add_widget(self.search_input)

        self.spinner = Spinner(text='Escolha uma criptomoeda', values=[], size_hint=(None, None), size=(400, 44))
        layout.add_widget(self.spinner)

        self.quantidade_input = TextInput(hint_text='Digite a quantidade de criptomoeda',
                                          multiline=False, input_type='number', input_filter='float')
        layout.add_widget(self.quantidade_input)

        self.moeda_spinner = Spinner(text='Escolha a moeda de conversão', values=self.moedas_fiat, size_hint=(None, None), size=(400, 44))
        layout.add_widget(self.moeda_spinner)

        self.resultado_label = Label(text='', halign='center', valign='middle', size_hint_y=None, height=40)
        layout.add_widget(self.resultado_label)

        self.valor_conversao_input = TextInput(hint_text='Valor convertido', multiline=False, readonly=True)
        layout.add_widget(self.valor_conversao_input)

        # Adicionando um botão de conversão
        self.botao_converter = Button(text='Converter Valor', size_hint=(None, None), size=(400, 44))
        self.botao_converter.bind(on_press=self.converter_callback)  # Vinculando o evento de pressionar ao método de conversão
        layout.add_widget(self.botao_converter)

        return layout

    def obter_lista_criptos(self):
        url = 'https://api.coingecko.com/api/v3/coins/list'
        resposta = requests.get(url)
        dados = resposta.json()
        return dados

    def atualizar_lista_criptos(self, instance):
        termo_pesquisa = instance.text.lower()
        nomes_filtrados = [cripto['name'] for cripto in self.lista_criptos if termo_pesquisa in cripto['name'].lower()]
        self.spinner.values = ['Escolha uma criptomoeda'] + nomes_filtrados
        self.spinner.text = 'Escolha uma criptomoeda'

    def obter_id_cripto(self, nome_cripto):
        for cripto in self.lista_criptos:
            if cripto['name'] == nome_cripto:
                return cripto['id']
        return None

    def converter_callback(self, instance):
        nome_cripto = self.spinner.text
        quantidade_moeda = self.quantidade_input.text
        moeda_conversao = self.moeda_spinner.text

        if nome_cripto == 'Escolha uma criptomoeda' or not quantidade_moeda or moeda_conversao not in self.moedas_fiat:
            self.mostrar_popup('Erro', 'Escolha uma criptomoeda, digite a quantidade e escolha a moeda de conversão.')
            return

        try:
            quantidade_moeda = float(quantidade_moeda)
        except ValueError:
            self.mostrar_popup('Erro', 'Digite uma quantidade válida.')
            return

        cripto_id = self.obter_id_cripto(nome_cripto)
        if cripto_id:
            valor_em_usd = self.obter_valor_cripto(quantidade_moeda, cripto_id)
            if valor_em_usd is not None:
                valor_em_moeda_conversao = self.converter_para_moeda_conversao(valor_em_usd, moeda_conversao)

                resultado_texto = f'O valor de {quantidade_moeda} {nome_cripto.upper()} é aproximadamente {format_currency(valor_em_usd, "USD", locale="en_US")}.\n'
                resultado_texto += f'Convertido para {moeda_conversao}, isso é aproximadamente {format_currency(valor_em_moeda_conversao, moeda_conversao, locale="pt_BR")}.'

                self.resultado_label.text = resultado_texto
                self.valor_conversao_input.text = str(format_currency(valor_em_moeda_conversao, moeda_conversao, locale="pt_BR"))  # Atualiza o TextInput com o valor convertido
            else:
                self.mostrar_popup('Erro', f'A criptomoeda com ID {cripto_id} não foi encontrada.')
        else:
            self.mostrar_popup('Erro', 'ID da criptomoeda não encontrado.')

    def obter_valor_cripto(self, quantidade, cripto_id):
        url = f'https://api.coingecko.com/api/v3/simple/price?ids={cripto_id}&vs_currencies=usd'
        resposta = requests.get(url)
        dados = resposta.json()

        if 'error' in dados:
            return None

        if cripto_id.lower() == 'usd':
            valor_em_usd = quantidade
        else:
            try:
                valor_em_usd = quantidade * dados[cripto_id]['usd']
            except KeyError:
                return None

        return valor_em_usd

    def converter_para_moeda_conversao(self, valor_em_usd, moeda_conversao):
        if moeda_conversao == 'USD':
            return valor_em_usd
        elif moeda_conversao in self.moedas_fiat:
            url = f'https://api.coingecko.com/api/v3/simple/price?ids=usd&vs_currencies={moeda_conversao.lower()}'
            resposta = requests.get(url)
            dados = resposta.json()

            if 'error' in dados:
                return None

            return valor_em_usd * dados['usd'][moeda_conversao.lower()]

    def mostrar_popup(self, titulo, mensagem):
        popup = Popup(title=titulo, content=Label(text=mensagem), size_hint=(None, None), size=(400, 200))
        popup.open()

if __name__ == '__main__':
    CryptoConverterApp().run()
