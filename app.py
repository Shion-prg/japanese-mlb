from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)
from bs4 import BeautifulSoup
import requests

app = Flask(__name__)

# LINE認証
line_bot_api = LineBotApi('YOUR_CHANNEL_ACCESS_TOKEN')
handler = WebhookHandler('YOUR_CHANNEL_SECRET')

# 選手のナンバー取得
player_data = BeautifulSoup(requests.get(
    'https://baseball.yahoo.co.jp/mlb/japanese/').text, 'html.parser').find_all('div', class_='playercard')
player_num = {}
for i in player_data:
    player_num[i.text.split()[2]] = i.find('a')['href'].lstrip(
        '/mlb/teams/player/pitcherfielder/profile/')


@app.route('/')
def test():
    return 'テスト'


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # print(total(event.message.text))
    message = event.message.text.split()
    text = record(message[0], message[1])
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=text))


if __name__ == "__main__":
    app.run()


def record(player, comment):
    pitcher = requests.get(
        'https://baseball.yahoo.co.jp/mlb/teams/player/pitcher/stats/{}'.format(player_num[player]))
    fielder = requests.get(
        'https://baseball.yahoo.co.jp/mlb/teams/player/fielder/stats/{}'.format(player_num[player]))

    pitcher_data = BeautifulSoup(pitcher.text, 'html.parser').find_all('tr')
    fielder_data = BeautifulSoup(fielder.text, 'html.parser').find_all('tr')

    if '年間成績' == comment:
        pitcher_result = {key: val for key, val in zip(
            pitcher_data[2].text.split() + pitcher_data[4].text.split(), Inning(pitcher_data[3].text.split() + pitcher_data[5].text.split()))} if pitcher_data[3].text.split()[2] != '-' else '登板なし'
        fielder_result = {key: val for key, val in zip(
            fielder_data[2].text.split() + fielder_data[4].text.split(), fielder_data[3].text.split() + fielder_data[5].text.split())} if pitcher_data[3].text.split()[2] != '0' else '出場なし'

    if '最近の成績' == comment:
        pitcher_result = {key: val for key, val in zip(
            pitcher_data[6].text.split(), Inning(THV(pitcher_data[7].text.split())))} if pitcher_data[3].text.split()[2] != '-' else '登板なし'
        fielder_result = {key: val for key, val in zip(
            fielder_data[6].text.split(), THV(fielder_data[7].text.split()))} if pitcher_data[3].text.split()[2] != '0' else '出場なし'

    text = '{}：{}\n'.format(player, comment)

    if pitcher_result != '登板なし':
        text += '投手成績\n'

        for key, value in pitcher_result.items():
            text += key + '：' + value + '\n'
    else:
        text += '投手成績：登板なし\n'

    if fielder_result != '出場なし':
        text += '\n野手成績\n'

        for key, value in fielder_result.items():
            text += key + '：' + value + '\n'
    else:
        text += '\n野手成績：出場なし'

    return text


# リストの修正
def THV(list):
    THV = '：'.join(list[1:3])
    del list[1:3]
    list.insert(1, THV)
    return list


def Inning(list):
    if len(list) == 19:
        Inning = ' '.join(list[8:10])
        del list[8:10]
        list.insert(8, Inning)
        return list
    elif len(list) == 17:
        Inning = ' '.join(list[9:11])
        del list[9:11]
        list.insert(9, Inning)
        return list
    else:
        return list
