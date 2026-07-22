# Sunucu ve Haritalarda Kullanım Rehberi

Bu rehber `siberanka/Text_Effects` v1.2.0 paketini Minecraft Java Edition 1.17.x–26.x istemcilerinde rütbe, prefix, başlık, actionbar ve harita metinlerinde kullanmak içindir.

## 1. Temel kural

Efekti seçen değer, görünen gradyan değil tetikleyici renktir. Örneğin kırmızı rütbe gradyanını göstermek için metni `#F8F8F0` yapın; shader bunu `#981818` → `#FF6868` olarak çizer.

- Renk tam eşleşmelidir. `#F8F8F0` yerine yakın bir renk çalışmaz.
- Bir metnin yalnızca istediğiniz bölümlerine tetikleyici renk verin.
- Plugin'in kendi gradient/rainbow özelliğini tetikleyici metinde kullanmayın; her harfe farklı RGB verirse eşleşme bozulur.
- Efekt istemcide çizilir. Sunucu yalnızca JSON metnini ve kaynak paketini gönderir.
- Tüm tetikleyiciler için [README renk tablosuna](./README.md#kaynak-paketteki-tüm-tetikleyici-renk-kodları) bakın.

## 2. Paketi istemciye kurma

1. Release sayfasından `Text-Effects-v1.2.0.zip` dosyasını indirin.
2. ZIP'i açmadan `.minecraft/resourcepacks/` içine koyun.
3. Minecraft'ta **Ayarlar → Kaynak Paketleri** ekranından etkinleştirin.
4. Paket 1.17–1.20.1'de eski istemcilerin metadata sınırlaması nedeniyle uyumsuz görünebilir. Uyarıyı onaylayıp yükleyin.
5. Başka bir paket `rendertype_text` shader'ını değiştiriyorsa yalnızca listede üstteki çalışır.

## 3. Sunucudan otomatik dağıtım

ZIP'i doğrudan HTTPS indirme bağlantısı veren bir adreste barındırın. GitHub release bağlantısı:

```text
https://github.com/siberanka/Text_Effects/releases/download/v1.2.0/Text-Effects-v1.2.0.zip
```

`server.properties` örneği:

```properties
resource-pack=https://github.com/siberanka/Text_Effects/releases/download/v1.2.0/Text-Effects-v1.2.0.zip
resource-pack-sha1=4886a87a3ac4ebc4aa0b88579b0b854412a24aa4
require-resource-pack=true
resource-pack-prompt={"text":"Rütbe gradyanlarını görebilmek için kaynak paketini kabul etmelisiniz.","color":"yellow"}
```

Dosya doğrulama değerleri:

```text
SHA-1   4886A87A3AC4EBC4AA0B88579B0B854412A24AA4
SHA-256 955E9C14866ECF3AF53F757492CDCE91DA1CF53E72A868DC8100A89AF5BBE3A2
```

Paketi değiştirdiğinizde ZIP'i yeniden üretin ve `resource-pack-sha1` değerini de değiştirin. Hash almak için:

```powershell
Get-FileHash -Algorithm SHA1 .\Text-Effects-v1.2.0.zip
```

```sh
sha1sum Text-Effects-v1.2.0.zip
```

Sunucuyu yeniden başlattıktan sonra temiz bir istemci profiliyle bağlanın. İstemci daha önce aynı URL'den farklı içerik önbelleğe aldıysa URL'ye yeni sürüm etiketi verin.

## 4. Haritaya gömülü kaynak paketi

Tek oyunculu veya indirilebilir bir haritada paketi dünya dosyasına gömebilirsiniz:

- Minecraft 1.17.x–1.21.11: ZIP'i `<dünya>/resources.zip` olarak koyun.
- Minecraft 26.1 ve sonrası: ZIP'i `<dünya>/resourcepacks/resources.zip` olarak koyun.

Release ZIP'ini yeniden ZIP'lemeyin. `resources.zip` açıldığında kökte doğrudan `pack.mcmeta` ve `assets/` görülmelidir. Haritayı birden fazla ana sürüm için yayımlıyorsanız iki konuma da aynı dosyayı koymak yerine her sürüm dağıtımını hedef sürümün beklediği konumla hazırlayın; aksi hâlde harita boyutu gereksiz yere iki katına çıkar.

## 5. Vanilla komut örnekleri

### Tellraw / sohbet duyurusu

```mcfunction
/tellraw @a {"text":"[ADMIN] ","color":"#F8F8F0","bold":true,"extra":[{"text":"Sunucu bakımı 10 dakika sonra.","color":"white","bold":false}]}
```

Yalnızca `[ADMIN]` kırmızı gradyan olur; devamındaki beyaz metin normal çizilir.

### Title ve actionbar

```mcfunction
/title @a title {"text":"VIP","color":"#F8F8E0","bold":true}
/title @a subtitle {"text":"Yeni rütben hayırlı olsun!","color":"white"}
/title @a actionbar {"text":"MAVİ TAKIM","color":"#F8F8E8","bold":true}
```

### Takım prefix'i

```mcfunction
/team add admin
/team modify admin prefix {"text":"[ADMIN] ","color":"#F8F8F0","bold":true}
/team join admin OyuncuAdi
```

`team color` yalnızca vanilla adlandırılmış renkleri kabul eder; gradyanı `prefix`/`suffix` JSON bileşeninde hex renk olarak verin.

### Text display

```mcfunction
/summon minecraft:text_display ~ ~2 ~ {text:'{"text":"EFSANEVİ","color":"#F8F8EC","bold":true}',billboard:"center",background:0,shadow:1b}
```

`text_display` Minecraft 1.19.4 ve sonrasında vardır. Komut bloğunda tırnak kaçışları, kullandığınız sürümün SNBT ayrıştırıcısına göre düzenlenebilir.

### Tabela, kitap ve item adı

Efekt, metin `rendertype_text` yoluyla çizildiği ve gerçek RGB tetikleyici korunabildiği sürece çalışır. Tabela/kitap/item JSON bileşeninde `"color":"#F8F8DC"` biçimini kullanın. Örs arayüzü veya yalnızca vanilla renk adı üreten bir plugin, özel hex rengi korumazsa efekt tetiklenmez.

## 6. Plugin ve rütbe sistemleri

### MiniMessage

Adventure/MiniMessage kullanan bir plugin'de tek ve sabit renk verin:

```text
<#F8F8F0><bold>[ADMIN]</bold></#F8F8F0>
<#F8F8E0><bold>[VIP]</bold></#F8F8E0>
<#F8F8E8><bold>[MAVI]</bold></#F8F8E8>
```

Şunu kullanmayın:

```text
<gradient:#F8F8F0:#F8F8F4>[ADMIN]</gradient>
```

İkinci örnek harf başına farklı renk üretir; shader'ın tam renk eşleşmesini bozar.

### LuckPerms / sohbet plugin'i

LuckPerms prefix değerini, onu ekrana basan sohbet/TAB plugin'inin desteklediği biçimde kaydedin. MiniMessage işleyen bir kurulum için tipik örnek:

```text
/lp group admin meta setprefix 100 "<#F8F8F0><bold>[ADMIN]</bold></#F8F8F0> "
```

LuckPerms yalnızca metayı saklar; formatı gerçekten parse eden bileşen EssentialsChat, TAB, LPC veya kullandığınız sohbet eklentisidir. Plugin legacy `&` kodlarını destekliyor ama hex desteklemiyorsa modern hex/MiniMessage seçeneğini açın.

### TAB / scoreboard

Header, footer, nametag prefix ve scoreboard satırlarında aynı tetikleyiciyi kullanabilirsiniz. Animasyon özelliği rengi periyodik değiştiriyorsa kapatın. Gradient'in tamamını istemci shader'ı ürettiği için TAB tarafında ikinci bir gradient tanımlamayın.

## 7. Önerilen rütbe eşlemeleri

| Rütbe örneği | Kod | Gradyan |
| --- | --- | --- |
| Kurucu / Owner | `#F8F8EC` | Lacivert → Açık lacivert |
| Admin | `#F8F8F0` | Kırmızı → Açık kırmızı |
| Moderatör | `#F8F8E8` | Mavi → Camgöbeği |
| VIP+ | `#F8F8E4` | Turuncu → Açık turuncu |
| VIP | `#F8F8E0` | Sarı → Açık sarı |
| Destekçi | `#F8F8F4` | Yeşil → Açık yeşil |
| Oyuncu | `#F8F8DC` | Gri → Beyaz |

## 8. Sorun giderme

### Metin tetikleyiciye yakın sarı/beyaz görünüyor

Paket yüklenmemiştir, shader derlenememiştir veya başka bir kaynak paketi `rendertype_text` dosyasını eziyordur. `logs/latest.log` içinde `rendertype_text`, `shader` ve `moj_import` arayın.

### Efekt çalışıyor ama bazı harfler normal

Plugin harf başına renk/gradient uyguluyordur. Oluşan JSON bileşenlerinin tamamının aynı tetikleyici RGB'yi taşıdığını doğrulayın.

### Gölge yanlış efekte dönüşüyor

Kendi tetikleyicinizi eklediyseniz RGB bileşenlerini dördün katı seçin ve başka tetikleyicilerin dörtte birlik gölge renkleriyle çakıştırmayın. Dahili doğrulayıcı bu çakışmaları denetler:

```sh
python scripts/validate_pack.py
```

### Iris, OptiFine veya başka shader/mod kullanıyorum

Bu paket vanilla çekirdek text shader'ını değiştirir. Render modları aynı shader yükleme yolunu değiştirebilir veya devre dışı bırakabilir. Önce modsuz vanilla profilde doğrulayın; sonra modları tek tek ekleyin.

### 1.17–1.20.1 “uyumsuz paket” uyarısı veriyor

Bu sürümler çok sürümlü `supported_formats` metadata alanını henüz tanımaz. Tek ZIP'in eski sürümlerde seçilebilir kalması için `pack_format` legacy fallback değeri korunur; uyarıyı onaylamak çalışma zamanındaki shader uyumluluğunu değiştirmez.

## 9. Teknik sürüm notları

Bu paket sınırları Mojang'ın değişiklikleriyle eşleşir:

- [Java 1.17](https://www.minecraft.net/en-us/article/caves---cliffs--part-i-out-today-java): kaynak paket formatı 7.
- [Java 1.20.2](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-20-2): `supported_formats` ve overlay sistemi.
- [Java 1.21.2](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-2): shader tanımı ve namespaced import değişiklikleri.
- [Java 1.21.6](https://www.minecraft.net/en-us/article/minecraft-java-edition-1-21-6): çekirdek shader uniform blokları.
- [Java 26.1](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-1): kaynak formatı 84 ve text/lightmap değişiklikleri.
- [Java 26.2](https://www.minecraft.net/en-us/article/minecraft-java-edition-26-2): eski `rendertype_text*` shader'larının birleşik `core/text` shader'ıyla değiştirilmesi.

Mojang'ın kendi notlarında çekirdek shader override'larının desteklenmeyen bir özellik olduğu açıkça belirtilir. Bu yüzden gelecekte yeni bir sürüm çıktığında metadata aralığına güvenmek yerine `scripts/verify_mojang_abi.py` ile resmî istemci JAR'larına karşı yeniden doğrulama yapılmalıdır.
