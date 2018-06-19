# Wio Node + Alexa ハンズオン

## Wio Nodeの部

### Wi-Fiアクセスポイントに接続

Wio Nodeを設定するスマートフォンを、会場に用意されたWi-Fiアクセスポイントに接続してください。  
（自動接続にしておく必要があります。）

### Wioサーバーにログイン

App Storeで`Wio Link`アプリ(以降、Wioアプリ)を検索して、インストールしてください。

![26](img/26.PNG)

Wioアプリを起動して、`SIGN UP`タブを選択、メールアドレスとパスワードを入力して、`SIGN UP`ボタンをクリックしてください。  
講師からWioサーバーの指示があった場合は、ここでServer Locationを変更しておいてください。

![27](img/27.png)
![28](img/28.png)

### Wio Nodeデバイスを追加

Wioアプリの`Device List`画面で、右上のプラスマークをクリックしてください。  
そして、`Wio Node`をクリックしてください。

![29](img/29.png)
![30](img/30.png)

すると、`Setup Your Wio Node`画面が表示されます。

![31](img/31.png)

Wio Nodeの`FUNC`ボタンを長押しして、青色LEDがフワフワと点滅することを確認してください。  
（ここでは、Wio NodeがWi-Fiアクセスポイントとして動作するよう設定しています。）

![32](img/32.png)

Wioアプリの`Setup Your Wio Node`画面はそのままにしておいて、スマートフォンのWi-Fi設定画面でWio Nodeのアクセスポイント（'Wio_xxxxxx'という名称）に接続してください。

![33](img/33.png)

Wioアプリに戻って、`Goto wifi list`をクリックしてください。

![34](img/34.png)

会場に用意されたWi-Fiアクセスポイントを選択して、パスワードを入力、`Join`をクリックしてください。

![35](img/35.png)
![36](img/36.png)

Wio Nodeの名前（任意）を入力して、`Start Wio-ing'をクリックしてください。

![37](img/37.png)

追加したWio Nodeが一覧に表示されれば成功です。

![38](img/38.png)

### Wio NodeデバイスにLEDモジュールを追加

Wio Nodeをクリックしてください。Wio Nodeデバイスの画面になります。  
左コネクタの`SELECT`をクリックして、`OUTPUT`タブの`Generic Digital Output`をクリックしてください。  
左コネクタに電球マークが表示されていることを確認してから、`Update Firmware`ボタンをクリックしてください。
そして、`OK`をクリックしてください。

![39](img/39.png)
![40](img/40.png)
![41](img/41.png)

左コネクタに電球マークが表示されていて、下のボタンが`View API`と表示されていれば正常です。

![42](img/42.png)

Wio Nodeの電源（USBケーブル）を外して、左コネクタにGrove-LEDを接続、Wio Nodeの電源をつないでください。

![43](img/43.png)

Wioアプリの`View API`ボタンをクリックして、`.../GenericDOutD0/onoff/[onoff]?...`と書かれたセクションの`Test Request`に`1`を入力、`POST`ボタンをクリックしてください。  
すると、LEDが点灯します。  
`Test Request`に`1`を入力するとLED点灯、`Test Request`に`0`を入力するとLED消灯です。
点灯/消灯できるか試してください。

![44](img/44.png)
![45](img/45.png)

### パソコンからLEDを制御

パソコンのWebブラウザで、`(WioサーバーURL)/v1/node/resources?access_token=(アクセストークン)`を開いてください。  
`(WioサーバーURL)`はWioアプリのSetting画面に表示された値、`(アクセストークン)`はView API画面で表示されたaccess_tokenを入力してください。  
すると、WebブラウザにWioアプリのView APIと同じ画面が表示されます。
`.../GenericDOutD0/onoff/[onoff]?...`と書かれたセクションで、LEDを点灯/消灯できるか試してください。

![46](img/46.png)
