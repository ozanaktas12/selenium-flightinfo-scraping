# Pegasus Flight Scraper ✈️

Bu proje, [Pegasus Havayolları](https://www.flypgs.com/kalkis-varis-bilgilerimiz) web sitesinden **kalkış/varış uçuş bilgilerini** otomatik olarak çekmek için geliştirilmiş bir **Selenium tabanlı scraper** içerir.  
Seçilen kalkış noktası, varış noktası ve tarih bilgisi girildiğinde, sistem arama yapar ve çıkan uçuş bilgilerini JSON formatında kaydeder.

---

## 🚀 Özellikler
- Kullanıcıdan **kalkış yeri**, **varış yeri** ve **tarih** bilgisi alır.  
- Selenium ile formu doldurup “Uçuş Ara” butonuna tıklar.  
- **Tarifeli kalkış**, **tahmini kalkış** ve **gerçek kalkış** saatlerini toplar.  
- Tüm uçuş verilerini `ucus_sonuclari.json` dosyasına yazar.  
- Türkçe karakterler için normalize edilmiş arama desteği vardır.  

---

## 🔧 Kurulum
1. Repoyu klonla:
   ```bash
   git clone https://github.com/ozanaktas12/pegasus-flight-scraper.git
   cd pegasus-flight-scraper
