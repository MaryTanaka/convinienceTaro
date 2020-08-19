import subprocess
import re

# remove_custom_emoji
# 絵文字IDは読み上げない
def remove_custom_emoji(text):
    pattern = r'<:[a-zA-Z0-9_]+:[0-9]+>'    # カスタム絵文字のパターン
    return re.sub(pattern,'',text)   # 置換処理

# urlAbb
# URLなら省略
def urlAbb(text):
    pattern = "https?://[\w/:%#\$&\?\(\)~\.=\+\-]+"
    return re.sub(pattern,'URL省略',text)   # 置換処理

# creat_WAV
# message.contentをテキストファイルに書き込み
def creat_WAV(inputText):
    # message.contentをテキストファイルに書き込み

    inputText = remove_custom_emoji(inputText)   # 絵文字IDは読み上げない

    inputText = urlAbb(inputText)   # URLなら省略
    input_file = 'input.txt'

    with open(input_file,'w',encoding='utf-8') as file:
        file.write(inputText)

    #open_jtalk = ['open_jtalk']
    #辞書のパス
    x = '/var/lib/mecab/dic/open-jtalk/naist-jdic'
    #ボイスファイルのパス
    m = '/usr/share/hts-voice/mei/mei_normal.htsvoice'
    #発声速度
    r = '1.0'
    #出力ファイル名
    ow = 'open_jtalk.wav'

    command = '-x {x} -m {m} -r {r} -ow {ow} {input_file}'

    args= {'x':x, 'm':m, 'r':r, 'ow':ow, 'input_file':input_file}

    cmd = command.format(**args)

    print(['open_jtalk', cmd])

    subprocess.run(['open_jtalk', '-x', x, '-m', m, '-r', r, '-ow', ow, 'input.txt'])

    print('success!')
    return True

if __name__ == '__main__':
    creat_WAV('テスト')