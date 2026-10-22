from pathlib import Path
from html import escape
import json

ROOT=Path(__file__).resolve().parent.parent
IMAGE_ASSETS=json.loads((ROOT/'website'/'image-assets.json').read_text())
CAROUSEL_SIZES='(max-width:360px) calc(100vw - 32px), (max-width:700px) calc(100vw - 40px), (max-width:960px) calc((100vw - 92px) * .48), (max-width:1204px) calc((100vw - 108px) * .48), 526px'
STRIP_SIZES='(max-width:700px) 86vw, 40vw'

def image_sources(photo,sizes,deferred=False):
 asset=IMAGE_ASSETS.get(photo)
 if not asset or not asset['variants']:
  raise ValueError(f'Missing optimized image: {photo}. Run website/optimize_images.py first.')
 variants=asset['variants']
 for variant in variants:
  if not (ROOT/variant['path']).is_file():
   raise ValueError(f"Missing preview: {variant['path']}. Run website/optimize_images.py first.")
 prefix='data-' if deferred else ''
 attrs={prefix+'src':'/'+variants[0]['path'],
        prefix+'srcset':', '.join(f"/{v['path']} {v['width']}w" for v in variants),
        'sizes':sizes,'data-fullsrc':'/'+photo}
 return ' '.join(f'{key}="{escape(value,quote=True)}"' for key,value in attrs.items())

services=[
 ('terraces','Террасы','Террасы','images/services/terrace-premium-townhouse-main-v1.jpg','Монтаж и демонтаж террас.','Устанавливаем и демонтируем террасы, настилы, ступени и ограждения. Обновляем изношенные элементы.',['Установка новой террасы','Демонтаж старой террасы','Настил, ступени и ограждения','Замена отдельных элементов'],['Примерные размеры и высота террасы','Фотографии места и существующей конструкции','Пожелания к материалу и ограждению']),
 ('drywall','Гипсокартон','Гипсокартон','images/services/drywall-premium-partition-v1.jpg','Все работы с гипсокартоном.','Монтируем перегородки, обшивку стен и потолки из гипсокартона. Подготавливаем поверхности к отделке.',['Перегородки и обшивка стен','Потолки из гипсокартона','Монтаж и демонтаж конструкций','Заделка швов и подготовка к отделке'],['Размеры помещения и план работ','Фотографии стен и потолка','Пожелания к конструкции и отделке']),
 ('flooring','Паркет и ламинат','Паркет и ламинат','images/services/flooring-parquet.jpg','Аккуратная укладка напольного покрытия.','Укладываем паркет и ламинат, демонтируем старое покрытие и устанавливаем плинтусы.',['Укладка паркета и ламината','Демонтаж старого покрытия','Подготовка основания','Установка плинтусов и порогов'],['Площадь и состояние пола','Выбранное покрытие или пожелания к нему','Фотографии помещения']),
 ('doors','Двери','Двери','images/services/doors-premium-flush-ivory-v1.jpg','Установка и демонтаж дверей.','Демонтируем старые двери и устанавливаем новые: полотно, коробку, наличники и фурнитуру.',['Демонтаж дверей и коробок','Установка новых дверей','Монтаж наличников и фурнитуры','Подгонка дверного блока'],['Количество и размеры проёмов','Тип дверей и фотографии','Нужен ли демонтаж старых дверей']),
 ('furniture','Сборка мебели','Сборка мебели','images/services/furniture-approved-wardrobe-main-v6.png','Соберём мебель у вас дома.','Собираем корпусную мебель, устанавливаем и регулируем дверцы, ящики и фурнитуру.',['Сборка шкафов и стеллажей','Сборка столов и другой корпусной мебели','Установка и регулировка дверец и ящиков','Разборка мебели при необходимости'],['Название или инструкция к мебели','Количество предметов и место сборки','Фотографии деталей, если сборка начата'])]

faqs=[('Можно обратиться с небольшой задачей?','Да. Расскажите, что нужно сделать: обновить отдельный элемент, выполнить отделку или построить террасу. Возможность выполнения обсудим по описанию и фотографиям.'),('Как узнать стоимость?','Стоимость зависит от объёма, состояния объекта, материалов и доступа к месту работ. Пришлите описание и примерные размеры — обсудим, что нужно уточнить для расчёта.'),('В каких городах вы работаете?','Работаем в Таллинне, Эстония. Если объект находится за пределами города, возможность выезда обсудим отдельно.'),('Нужно ли покупать материалы заранее?','Лучше сначала обсудить задачу. Выбор, количество, покупку и доставку материалов согласовывают до начала работ.'),('Можно ли жить в квартире во время ремонта?','Это зависит от состава работ и состояния помещения. Укажите, будет ли квартира жилой во время ремонта, чтобы обсудить порядок работ.'),('Что подготовить для первого разговора?','Короткое описание, место проведения работ, примерные размеры и желаемые сроки. Фотографии можно приложить к письму в вашей почтовой программе.'),('Как согласовать сроки?','Укажите желаемый период. Возможную дату начала и продолжительность нужно согласовать после уточнения объёма работ.'),('Как отправить заявку?','Позвоните, напишите email или заполните форму на сайте. Сейчас форма готовит письмо в вашей почтовой программе; его нужно отправить самостоятельно.')]
nav=[('/services/','Услуги'),('/prices/','Цены'),('/about/','О нас'),('/contact/','Контакты')]

# Starting rates supplied by LAN OÜ. Keep the overview and service sections in sync.
price_rows=[
 ('Террасы','70 €','м²','terraces'),
 ('Гипсокартон','16 €','м²','drywall'),
 ('Паркет и ламинат','10 €','м²','flooring'),
 ('Двери — установка','50 €','дверь','doors'),
 ('Двери — демонтаж','20 €','дверь','doors'),
 ('Сборка мебели','20 €','час','furniture'),
]
service_prices={
 'terraces':('70 €','/ м²','Стоимость зависит от площади и состава работ по монтажу или демонтажу.'),
 'drywall':('16 €','/ м²','Итоговая цена зависит от конструкции, площади и подготовки поверхности.'),
 'flooring':('10 €','/ м²','Итоговая цена зависит от покрытия, основания и объёма работ.'),
 'doors':('50 €','/ дверь','Стоимость зависит от проёма, дверного блока и фурнитуры.'),
 'furniture':('20 €','/ час','Стоимость зависит от количества и сложности предметов мебели.'),
}
service_detail_copy={
 'terraces':(
  'Монтаж, обновление и демонтаж террас в Таллинне и Харьюмаа.',[
   ('Новая терраса','Поможем устроить место для отдыха рядом с домом. Выполняем монтаж террасного настила, ступеней и ограждений. Размеры, высоту конструкции и материал обсуждаем для вашего участка.'),
   ('Обновление','Если терраса уже есть, можно заменить изношенные доски, обновить ступени или ограждение. Сначала посмотрим на состояние существующей конструкции и уточним, какие элементы требуют работы.'),
   ('Демонтаж','Старую террасу можно демонтировать перед установкой новой. Объём демонтажа зависит от размеров, креплений и состояния основания; эти детали обсудим вместе с дальнейшими работами.'),
   ('Что нужно для расчёта','Пришлите примерные размеры и несколько фотографий места. Если есть пожелания к материалу, ступеням или ограждению, расскажите о них — так проще определить состав работ и стоимость.')]),
 'drywall':(
  'Работы с гипсокартоном для квартир и домов в Таллинне и Харьюмаа.',[
   ('Перегородки','Монтируем перегородки из гипсокартона, когда нужно разделить пространство или изменить планировку комнаты. Размеры и расположение новой конструкции уточняем до начала работ.'),
   ('Стены и потолки','Обшиваем стены и устраиваем потолки из гипсокартона. Обсудим каркас, сложные участки, количество поверхностей и результат, который вы хотите получить.'),
   ('Подготовка к отделке','После монтажа можно подготовить поверхность к следующему этапу: заделать швы и выполнить необходимые подготовительные работы. При необходимости обсудим демонтаж старой конструкции.'),
   ('Что нужно для расчёта','Полезны примерные размеры помещения, фотографии стен или потолка и короткое описание задачи. Если плана пока нет, просто расскажите, какую часть комнаты хотите изменить.')]),
 'flooring':(
  'Укладка паркета и ламината в Таллинне и Харьюмаа.',[
   ('Новое покрытие','Укладываем паркет и ламинат в жилых помещениях. Перед работой уточняем площадь, выбранный материал и планировку комнаты, чтобы согласовать порядок укладки.'),
   ('Старый пол','Если существующее покрытие нужно снять, обсудим демонтаж и состояние основания. От этого зависит подготовка пола перед укладкой нового материала.'),
   ('Завершение работы','Помимо самого покрытия, можно обсудить плинтусы и переходы между помещениями. Количество примыканий, порогов и сложных участков влияет на объём работ.'),
   ('Что нужно для расчёта','Пришлите примерную площадь и фотографии существующего пола. Если паркет или ламинат уже куплен, укажите его тип и размеры планок.')]),
 'doors':(
  'Установка и демонтаж дверей в Таллинне и Харьюмаа.',[
   ('Установка','Устанавливаем дверное полотно, коробку, наличники и фурнитуру. Перед монтажом уточняем размеры проёма, тип двери и то, какие элементы входят в комплект.'),
   ('Демонтаж','Если старую дверь нужно убрать, демонтаж можно обсудить отдельно от установки новой. Состояние проёма и креплений помогает понять объём работы.'),
   ('Несколько дверей','Можно обратиться с заменой одной двери или сразу нескольких дверей в квартире. Для каждой уточним размеры, комплектующие и необходимость демонтажа.'),
   ('Что нужно для расчёта','Сообщите количество дверей и примерные размеры проёмов. Фотографии существующих дверей и новых комплектов помогут быстрее обсудить стоимость и порядок работ.')]),
 'furniture':(
  'Сборка мебели для дома и квартиры в Таллинне и Харьюмаа.',[
   ('Что собираем','Собираем шкафы, стеллажи, столы и другую корпусную мебель. Можно обратиться с одним предметом или с несколькими комплектами для разных комнат.'),
   ('Детали и фурнитура','Устанавливаем полки, дверцы, ящики и фурнитуру, затем проверяем их работу. Конструкция и количество деталей влияют на время сборки.'),
   ('Если сборка уже начата','Расскажите, если мебель частично собрана или её нужно разобрать перед перемещением. Это поможет заранее понять состояние деталей и состав задачи.'),
   ('Что нужно для расчёта','Пришлите название или ссылку на модель, инструкцию и количество предметов. Укажите место сборки и сообщите, потребуется ли разборка старой мебели.')]),
}

def price_overview():
 rows=''.join(f'<tr><th scope="row"><a href="#{slug}">{work}</a></th><td><span class="price-table-from">от </span><strong>{amount}</strong><span class="price-unit"> / {unit}</span></td></tr>' for work,amount,unit,slug in price_rows)
 return '<div class="price-table-wrap"><table class="price-table"><caption class="visually-hidden">Стартовые цены на услуги LAN OÜ</caption><thead><tr><th scope="col">Услуга</th><th scope="col">Стоимость</th></tr></thead><tbody>'+rows+'</tbody></table></div>'
def price_badges(slug):
 if slug=='doors':
  labels={'Двери — установка':'Установка','Двери — демонтаж':'Снятие'}
  return ' '.join(f'<a class="service-rate service-rate--door" href="#prices"><span class="service-rate-kind">{labels[work]}</span> <span class="service-rate-amount"><span class="service-rate-from">от</span> <strong>{escape(amount)}</strong><span class="service-rate-unit"> / {escape(unit)}</span></span></a>' for work,amount,unit,key in price_rows if key==slug)
 amount,unit,_=service_prices[slug]
 return f'<a class="service-rate" href="#prices"><span class="service-rate-amount"><span class="service-rate-from">от</span> <strong>{escape(amount)}</strong><span class="service-rate-unit"> {escape(unit)}</span></span></a>'

PHONE_ICON='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3H4a1 1 0 0 0-1 1c0 9.4 7.6 17 17 17a1 1 0 0 0 1-1v-3l-5-2-2 2a14 14 0 0 1-7-7l2-2-2-5Z"/></svg>'
def cta(service='Другая задача',label='Обсудить задачу'):
 from urllib.parse import quote
 if label == 'Бесплатная консультация':
  return f'<a class="button consultation-call" href="tel:+3725232477">{PHONE_ICON}<span>{label}</span></a>'
 return f'<a class="button" href="/contact/?service={quote(service)}">{label}<span aria-hidden="true">↗</span></a>'
def gallery_photos():
 return {
  'terraces':[
   ('images/services/terrace-premium-townhouse-main-v1.jpg','Терраса у таунхауса со светлым диваном','50% 50%'),
   ('images/services/terrace-premium-penthouse-brown-v1.jpg','Терраса пентхауса с тёмным деревянным настилом','50% 50%'),
   ('images/services/terrace-premium-townhouse-brick-v1.jpg','Терраса со ступенями у кирпичного таунхауса','50% 50%'),
   ('images/services/terrace-premium-installation-v1.jpg','Монтаж деревянной террасы у таунхауса','50% 50%'),
   ('images/services/terrace-premium-penthouse-light-v1.jpg','Светлая деревянная терраса пентхауса','50% 50%')],
  'drywall':[
   ('images/services/drywall-premium-partition-v1.jpg','Перегородки и ниши из гипсокартона в светлом интерьере','50% 50%'),
   ('images/services/drywall-premium-ceiling-v1.jpg','Монтаж многоуровневого потолка из гипсокартона','50% 50%'),
   ('images/services/drywall-premium-lining-v1.jpg','Обшивка стен и скатов мансарды гипсокартоном','50% 50%'),
   ('images/services/drywall-premium-moisture-v1.jpg','Влагостойкий гипсокартон и ниши в ванной комнате','50% 50%'),
   ('images/services/drywall-premium-finishing-v1.jpg','Профессиональная заделка швов гипсокартона','50% 50%')],
  'flooring':[
   ('images/services/flooring-parquet.jpg','Паркетный пол','50% 100%'),
   ('images/services/flooring-premium-wide-oak-v1.jpg','Широкая дубовая доска в светлой гостиной','50% 50%'),
   ('images/services/flooring-premium-smoked-parquet-v1.jpg','Тёмный дубовый паркет в классическом интерьере','50% 50%'),
   ('images/services/flooring-premium-laminate-v1.jpg','Светлый ламинат в современной кухне-столовой','50% 50%'),
   ('images/services/flooring-premium-finish-detail-v1.jpg','Аккуратное примыкание пола к плинтусу и дверному проёму','50% 50%')],
  'doors':[
   ('images/services/doors-premium-flush-ivory-v1.jpg','Скрытая межкомнатная дверь под покраску','50% 50%'),
   ('images/services/doors-premium-oak-double-v1.jpg','Двустворчатые дубовые межкомнатные двери','50% 50%'),
   ('images/services/doors-premium-classic-closed-v2.jpg','Классическая филёнчатая дверь с латунной ручкой','50% 50%'),
   ('images/services/doors-premium-exterior-house-v2.jpg','Утеплённая стальная входная дверь в частном доме','50% 50%'),
   ('images/services/doors-premium-apartment-security-v2.jpg','Входная дверь в квартиру с усиленной коробкой и двумя замками','50% 50%')],
  'furniture':[
   ('images/services/furniture-approved-wardrobe-main-v6.png', 'Сборка шкафа: установка дверей и фурнитуры', '85% 100%'),
   ('images/services/furniture-approved-oak-wardrobe-v5.jpg', 'Сборка дубового шкафа с полками и дверцами', '90% 100%'),
   ('images/services/furniture-approved-kitchen-v5.jpg', 'Сборка кухонных шкафов и установка мебельных петель', '65% 100%'),
   ('images/services/furniture-approved-chair-v5.jpg', 'Сборка офисного кресла: детали, крепления и механизм', '55% 85%'),
   ('images/services/furniture-approved-sofa-v5.jpg', 'Сборка модульного дивана: соединение секций и крепление ножек', '50% 90%')]
 }


def photo_preview_style(photo,position):
 # Focus on the construction detail at thumbnail size; the lightbox uses the full original.
 focus={
  'images/services/furniture-approved-wardrobe-main-v6.png':('85% 100%', 1.5, 1.45),
  'images/services/furniture-approved-oak-wardrobe-v5.jpg':('90% 100%', 1.25, 1.2),
  'images/services/furniture-approved-kitchen-v5.jpg':('65% 100%', 1.25, 1.2),
  'images/services/furniture-approved-chair-v5.jpg':('55% 85%', 1.12, 1.08),
  'images/services/furniture-approved-sofa-v5.jpg':('50% 90%', 1.18, 1.12),
  'images/services/drywall-real-interior.jpg':('70% 10%',1.08,1.18),
  'images/services/drywall-real-joint-finishing.jpg':('50% 0%',1.14,1.25),
  'images/services/drywall-real-moisture-board.jpg':('65% 50%',1,1),
  'images/services/drywall-real-renovation.jpg':('50% 50%',1,1),
  'images/services/drywall-real-small-room.jpg':('50% 12%',1,1),

 }
 style=f'object-position:{position}'
 if photo in focus:
  origin,zoom,mobile_zoom=focus[photo]
  style+=f';--preview-origin:{origin};--preview-zoom:{zoom};--preview-mobile-zoom:{mobile_zoom}'
 return style

def carousel_image(slug,index,photo,alt,position):
 loading=('loading="eager" fetchpriority="high"' if slug=='terraces' else 'loading="lazy"') if index==0 else ''
 return f'<img {image_sources(photo,CAROUSEL_SIZES,deferred=index!=0)} {loading} alt="{alt} — иллюстрация услуги" style="{photo_preview_style(photo,position)}" decoding="async" width="640" height="420" draggable="false" aria-hidden="{str(index!=0).lower()}" class="carousel-slide{ " is-active" if index==0 else ""}">'

def rows():
 galleries=gallery_photos()
 result=[]
 for slug,title,key,img,tag,desc,scope,prep in services:
  photos=galleries[slug]
  slides=''.join(carousel_image(slug,i,photo,alt,position) for i,(photo,alt,position) in enumerate(photos))
  gallery=f'<div class="service-carousel{" is-single" if len(photos)==1 else ""}" data-gallery="{slug}" role="region" aria-roledescription="карусель" aria-label="{title}: фотографии"><div class="carousel-viewport">{slides}</div><button type="button" class="carousel-open" aria-label="Увеличить фотографию: {title}" aria-haspopup="dialog"><span class="carousel-zoom-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.3 15.3 5 5M10.5 7.5v6M7.5 10.5h6"/></svg></span></button><button type="button" class="carousel-prev carousel-direction" aria-label="Предыдущее фото"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 5-7 7 7 7"/></svg></button><button type="button" class="carousel-next carousel-direction" aria-label="Следующее фото"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 5 7 7-7 7"/></svg></button></div>'
  check_icon='<svg viewBox="0 0 24 24" aria-hidden="true" focusable="false"><path d="m5 12 4 4L19 6"/></svg>'
  highlights='<ul class="service-highlights" role="list">'+''.join(f'<li>{check_icon}<span>{escape(item)}</span></li>' for item in scope)+'</ul>'
  choices_class='service-action service-choices'+(' service-choices--doors' if slug=='doors' else '')
  result.append(f'<article class="service-row service-row--listed">{gallery}<div class="service-copy"><h3>{title}</h3>{highlights}<span class="{choices_class}"><a class="service-button service-price" href="#{slug}">Подробнее</a>{price_badges(slug)}<a class="service-button service-call" href="tel:+3725232477"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 3H4a1 1 0 0 0-1 1c0 9.4 7.6 17 17 17a1 1 0 0 0 1-1v-3l-5-2-2 2a14 14 0 0 1-7-7l2-2-2-5Z"/></svg>Бесплатная консультация</a></span></div></article>')
 return ''.join(result)
def accordion(items):
 return ''.join(f'<details><summary>{q}</summary><p>{a}</p></details>' for q,a in items)
def band():
 return '<section class="contact-band"><div><p class="eyebrow">ЕСТЬ ЗАДАЧА?</p><h2>Давайте обсудим ваш дом.</h2><p>Начните с короткого описания или звонка.</p></div>'+cta()+'</section>'
PAGES = {}
def page(path,title,description,body):
 PAGES[path] = (title,description,body)
page('/','Работы для вашего дома','Террасы, гипсокартон, паркет и ламинат, двери, сборка мебели в Таллинне и Харьюмаа.', '<section class="home-intro"><div><h1>Строительные и отделочные работы в Таллинне и Харьюмаа</h1><p class="home-promise">Просто позвоните нам, всё остальное мы сделаем сами</p><p class="home-summary">LAN OÜ выполняет строительные и отделочные работы для дома и квартиры в Таллинне и Харьюмаа. Устанавливаем и демонтируем террасы, обновляем настил, ступени и ограждения. Монтируем перегородки, обшивку стен и потолки из гипсокартона, укладываем паркет и ламинат, устанавливаем и демонтируем двери, собираем шкафы и другую корпусную мебель. Берёмся за отдельные задачи и несколько работ на одном объекте. Перед началом обсуждаем объём, материалы и стоимость. За нашей работой — 20 лет опыта в строительстве и ремонте.</p></div></section><section>'+rows()+'<article class="service-row other-service"><img src="/images/services/other-task.svg" alt="" width="640" height="420"><div><h3>Другая задача</h3><p>Не нашли нужную услугу? Опишите, что вы хотите сделать для дома или участка — обсудим, чем можем помочь.</p><span class="service-action"><a class="service-button service-price" href="#description" data-service="Другая задача">Описать свою задачу</a></span></div></article></section><section class="section"><div class="section-heading"><h2>От задачи к результату</h2><a href="/process/">Как работаем ↗</a></div><div class="steps"><article><span>Обсуждение</span><h3>Расскажите, что нужно</h3><p>Описание, фотографии и место проведения работ помогут начать разговор.</p></article><article><span>Подготовка</span><h3>Уточним детали</h3><p>Объём, материалы, стоимость и сроки обсуждаются до начала работ.</p></article><article><span>Работа</span><h3>Согласуем следующий шаг</h3><p>Выезд, подготовку и порядок выполнения определяем для вашей задачи.</p></article></div></section><section class="section narrow"><h2>Частые вопросы</h2>'+accordion(faqs[:3])+'<a class="text-link" href="/faq/">Все вопросы и ответы ↗</a></section>'+band())
page('/services/','Услуги','Террасы, гипсокартон, паркет и ламинат, двери, сборка мебели. Выберите направление работ.', '<section class="page-intro"><p class="eyebrow">ЧЕМ МОЖЕМ ПОМОЧЬ</p><h1>Работы для дома.<br><em>Большие и небольшие.</em></h1><p class="lead">Выберите направление, чтобы узнать подробности и подготовить обращение.</p></section>'+rows()+'<a class="other-row" href="/contact/?service=Другая%20задача">Не нашли свою задачу? Расскажите о ней ↗</a><p class="photo-note">Фотографии иллюстрируют направления работ.</p>'+band())
for slug,title,key,img,tag,desc,scope,prep in services:
 page('/services/'+slug+'/',title,desc, f'<section class="detail-hero"><div><p class="eyebrow">УСЛУГИ LAN OÜ</p><h1>{title}</h1><p class="lead">{tag}</p><p>{desc}</p>'+cta(key)+'</div><figure><img src="/'+img+'" alt="Иллюстрация: '+title.lower()+'" width="640" height="420"><figcaption>Иллюстрация направления работ.</figcaption></figure></section><section class="two-column section"><div><h2>Какие задачи обсудим</h2><ul class="lined-list">'+''.join('<li>'+x+'</li>' for x in scope)+'</ul></div><div><h2>Что подготовить</h2><ul class="lined-list">'+''.join('<li>'+x+'</li>' for x in prep)+'</ul><p class="muted">Нет точных размеров? Начните с описания — уточним детали в разговоре.</p></div></section><section class="info-block"><h2>Стоимость и сроки</h2><p>Зависят от объёма работ, материалов и состояния объекта. Укажите населённый пункт и желаемые сроки: обсудим возможность выезда и данные для расчёта.</p>'+cta(key,'Обсудить стоимость')+'</section><section class="section"><h2>Другие направления</h2><div class="related">'+''.join(f'<a href="/services/{a}/">{b} ↗</a>' for a,b,*_ in services if a!=slug)+'</div></section>')
page('/about/','О нас','LAN OÜ — террасы, гипсокартон, паркет и ламинат, двери, сборка мебели в Таллинне и Харьюмаа.', '<div class="company-about"><h1 class="section-title">О нас</h1><div class="company-about-grid"><div class="company-about-copy"><p>LAN OÜ выполняет строительные и ремонтные работы для дома и участка в Таллинне и Харьюмаа.</p><p>Устанавливаем и демонтируем террасы и двери, выполняем работы с гипсокартоном, укладываем паркет и ламинат, собираем мебель. Берёмся за отдельные задачи и несколько работ на одном объекте.</p><p>За нашей работой — 20 лет опыта в строительстве и ремонте. До начала работ согласуем объём, материалы, стоимость и сроки.</p></div><dl class="company-details"><div><dt>Название компании</dt><dd>LAN OÜ</dd></div><div><dt>Регистрационный код</dt><dd>17505187</dd></div><div><dt>Владелец</dt><dd>Anatoli Lebjodkin</dd></div></dl></div></div>')
page('/process/','Как работаем','Как обсудить задачу, уточнить объём и подготовиться к работам.', '<section class="page-intro"><p class="eyebrow">ПОНЯТНЫЙ ПОРЯДОК</p><h1>Сначала детали.<br><em>Потом работа.</em></h1><p class="lead">Что стоит обсудить, прежде чем приступать к вашему объекту.</p></section><div class="process-list">'+''.join(f'<section><h2>{a}</h2><p>{b}</p></section>' for a,b in [('Расскажите о задаче','Выберите услугу или опишите другую задачу. Укажите населённый пункт, примерные размеры и желаемый период.'),('Уточним состояние объекта','Фотографии помогают понять исходную ситуацию. Если нужен осмотр, возможность и время выезда согласовываются отдельно.'),('Обсудим условия','До начала уточняются состав работ, материалы, стоимость и сроки. Отдельно стоит обсудить доступ к объекту, доставку и уборку.'),('Согласуем выполнение','Порядок работ зависит от задачи и условий на объекте. Изменения объёма или материалов нужно обсудить до их выполнения.'),('Проверим результат','После выполнения стоит вместе проверить согласованный объём и обсудить уход за материалами, если это необходимо.')])+'</div>'+band())
page('/faq/','Вопросы и ответы','Ответы на вопросы о стоимости, сроках, материалах и обращении в LAN OÜ.', '<section class="page-intro"><p class="eyebrow">ПЕРЕД НАЧАЛОМ</p><h1>Вопросы <em>и ответы.</em></h1><p class="lead">Если вашей ситуации здесь нет, свяжитесь с нами.</p></section><label class="search-label" for="faq-search">Найти ответ</label><input type="search" id="faq-search" placeholder="Например, материалы или сроки"><div id="faq-list">'+accordion(faqs)+'</div><p id="faq-empty" hidden role="status">Совпадений нет. Попробуйте другое слово или напишите нам.</p>'+band())
options=''.join('<option>'+x+'</option>' for x in ['Террасы','Гипсокартон','Паркет и ламинат','Двери','Сборка мебели','Другая задача'])
page('/contact/','Контакты','Свяжитесь с LAN OÜ, чтобы обсудить задачу.', '<section class="page-intro"><h1 class="section-title">Контакты</h1></section><div class="contact-layout"><aside class="contact-direct"><img class="contact-portrait" src="/images/about/anatoli-portrait.png" alt="Anatoli Lebjodkin — владелец LAN OÜ" width="1086" height="1448" loading="lazy" decoding="async"><div class="contact-profile"><h2>Anatoli Lebjodkin</h2><p>Владелец LAN OÜ</p></div><a class="button consultation-call contact-profile-call" href="tel:+3725232477">PHONEICON<span>Позвонить</span></a></aside><form id="request-form" method="post" enctype="multipart/form-data"><div class="form-honeypot" hidden aria-hidden="true"><label for="website-url">Website</label><input id="website-url" name="_honey" type="text" tabindex="-1" autocomplete="off"></div><h2>Или оставьте заявку</h2><label for="service">Услуга *</label><select id="service" name="service" required><option value="" disabled selected>Выберите услугу</option>OPTIONS</select><label for="name">Ваше имя</label><input id="name" name="name" autocomplete="name" maxlength="100"><fieldset class="contact-preference"><legend>Как с вами связаться?</legend><div class="contact-preference-options"><label><input type="radio" name="contact_method" value="По телефону" checked>По телефону</label><label><input type="radio" name="contact_method" value="По email">По email</label></div></fieldset><div id="phone-reply-field"><label for="customer-phone">Ваш телефон *</label><input id="customer-phone" name="phone" type="tel" autocomplete="tel" required maxlength="40" placeholder="5123 4567"></div><div id="email-reply-field" hidden><label for="customer-email">Ваш email *</label><input id="customer-email" name="email" type="email" autocomplete="email" disabled maxlength="254"></div><label for="location">Где находится объект? *</label><select id="location" name="location" required><option value="" disabled selected>Выберите местоположение</option><option value="Tallinn">Tallinn</option><option value="Harjumaa">Harjumaa</option><option value="Muu">Muu</option></select><label for="timing">Когда хотите начать?</label><select id="timing" name="timing"><option>Пока не определился</option><option>В ближайшее время</option><option>В течение 1–3 месяцев</option><option>Позже</option></select><label for="description">Что нужно сделать? *</label><textarea id="description" name="description" rows="5" required maxlength="2500" placeholder="Расскажите о задаче, примерных размерах и желаемых сроках"></textarea><div class="attachments"><label for="attachments">Фотографии или документы</label><p id="attachment-help" class="form-note">До 5 файлов, суммарно до 10 МБ. JPG, PNG, WebP, HEIC или PDF.</p><input id="attachments" type="file" multiple accept=".jpg,.jpeg,.png,.webp,.heic,.heif,.pdf" aria-describedby="attachment-help attachment-status"><ul id="attachment-list" aria-label="Выбранные файлы"></ul><p id="attachment-status" role="status"></p></div><p class="form-note">* Обязательные поля.</p><div id="contact-captcha" hidden><div id="contact-captcha-widget"></div><p id="captcha-status" role="status" aria-live="polite"></p><button id="captcha-retry" class="text-button" type="button" hidden>Повторить проверку</button></div><p class="form-note captcha-disclosure">Форма защищена Cloudflare Turnstile. <a href="#privacy">Обработка данных заявки</a>.</p><button class="button" type="submit" disabled>Отправить заявку</button><noscript><p>Для отправки формы включите JavaScript в браузере.</p></noscript><p id="form-status" role="status"></p></form></div>'.replace('PHONEICON',PHONE_ICON).replace('OPTIONS',options))
page('/privacy/','Данные обращения','Как обрабатываются заявки.', '<section class="page-intro"><h1>Данные <em>обращения.</em></h1></section><section class="narrow prose"><h2>Что передаётся</h2><p>Форма отправляет имя, предпочтительный способ связи, телефон или email, выбранную услугу, местоположение, сроки, описание задачи и вложения в LAN OÜ. Указывайте только данные, необходимые для обсуждения работ.</p><h2>Доставка заявки</h2><p>Сервер сайта передаёт заявку через настроенный почтовый сервис. Сайт не хранит архив обращений. Вложения временно обрабатываются при отправке. Почтовый сервис обрабатывает письмо по своим правилам.</p><h2>Защита от ботов</h2><p>Форма использует Cloudflare Turnstile для защиты от автоматических отправок. Cloudflare обрабатывает IP-адрес и технические данные браузера для этой проверки.</p><p><a href="https://www.cloudflare.com/turnstile-privacy-policy/" target="_blank" rel="noopener noreferrer">Обработка данных Turnstile</a> · <a href="https://www.cloudflare.com/privacypolicy/" target="_blank" rel="noopener noreferrer">Политика конфиденциальности Cloudflare</a></p><h2>По вопросам обращения</h2><p>LAN OÜ, регистрационный код 17505187. <a href="mailto:lebjodkin.toll68@gmail.com">Написать email</a>.</p></section>')


# Compose the content once, with native fragment navigation.
import re
from urllib.parse import urlsplit, parse_qs

def section_content(path):
 body=PAGES[path][2].replace(band(),'')
 body=body.replace('<h2','<h3').replace('</h2>','</h3>')
 return body.replace('<h1','<h2').replace('</h1>','</h2>')

home=PAGES['/'][2].split('<section class="section">',1)[0]
home=home.replace('<section>'+rows(),'<section id="services" aria-label="Услуги">'+rows())
details=''
all_gallery_photos=gallery_photos()
for slug,title,key,img,tag,desc,scope,prep in services:
 lead,topics=service_detail_copy[slug]
 cards=''.join(f'<article class="service-detail-card"><h3>{heading}</h3><p>{copy}</p></article>' for heading,copy in topics)
 photos=''.join(f'<button type="button" class="service-photo" data-photo-index="{i}" aria-label="Открыть фото {i+1}: {alt}"><img {image_sources(photo,STRIP_SIZES)} alt="{alt} — иллюстрация услуги" loading="lazy" decoding="async" draggable="false" width="400" height="250" style="{photo_preview_style(photo,position)}"></button>' for i,(photo,alt,position) in enumerate(all_gallery_photos[slug]))
 photo_strip=f'<div class="service-photo-strip" data-service-gallery="{slug}" role="group" aria-label="Фотографии: {title}. Прокрутите по горизонтали">{photos}</div>'
 details+=f'<section id="{slug}" class="service-detail section" aria-labelledby="{slug}-title"><div class="service-detail-heading"><h2 id="{slug}-title">{title}</h2><p class="lead">{lead}</p></div><div class="service-detail-cards">{cards}</div>{photo_strip}</section>'
body=home+'<div class="service-details">'+details+'</div>'
body+='<section id="prices" class="long-section" aria-labelledby="prices-title"><div class="page-intro"><h2 id="prices-title" class="section-title">Цены</h2></div>'+price_overview()+'<div class="price-footer"><p>Цены указаны <strong>«от»</strong>. Окончательную стоимость согласуем после уточнения объёма, материалов и состояния объекта.</p>'+cta("Другая задача","Бесплатная консультация")+'</div></section>'

for key in ['about','contact']:
 content=section_content('/'+key+'/')
 if key=='contact':
  privacy=PAGES['/privacy/'][2].split('</section>',1)[1].replace('<h2','<h3').replace('</h2>','</h3>')
  content+='<details id="privacy" class="contact-privacy"><summary>Обработка данных заявки</summary>'+privacy+'</details>'
 body+=f'<section id="{key}" class="long-section" aria-label="{PAGES["/"+key+"/"][0]}">'+content+'</section>'

links=''.join(f'<a href="#{path.strip("/")}">{label}</a>' for path,label in nav)
html=f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#087d53"><link rel="icon" type="image/vnd.microsoft.icon" sizes="16x16 32x32 48x48" href="/images/brand/favicon.ico?v=1"><link rel="icon" type="image/png" sizes="16x16" href="/images/brand/favicon-16.png?v=1"><link rel="icon" type="image/png" sizes="32x32" href="/images/brand/favicon-32.png?v=1"><link rel="icon" type="image/svg+xml" sizes="any" href="/images/brand/favicon.svg?v=1"><link rel="apple-touch-icon" sizes="180x180" href="/images/brand/apple-touch-icon.png?v=1"><title>Ремонт и отделочные работы в Таллинне и Харьюмаа | LAN Ehitus</title><meta name="description" content="LAN OÜ: террасы, гипсокартон, укладка паркета и ламината, установка дверей и сборка мебели в Таллинне и Харьюмаа. 20 лет опыта. Обсудим вашу задачу."><link rel="stylesheet" href="/website.css?v=prices-28"><script src="/website.i18n.js?v=captcha-22" defer></script><script src="/website.js?v=gallery-23" defer></script></head><body id="top"><a class="skip" href="#main">Перейти к содержанию</a><header><div class="header-inner wrap"><a class="brand" href="/" data-scroll-top aria-label="LAN Ehitus — в начало"><img src="/images/brand/lan-ehitus-original.jpeg?v=1" width="373" height="284" alt="LAN Ehitus"></a><button class="menu-button" aria-expanded="false" aria-controls="navigation" aria-label="Открыть меню"><span></span><span></span><span></span></button><nav id="navigation" aria-label="Основная навигация">{links}<details class="language-picker"><summary aria-label="Выбор языка: эстонский">ET</summary><div class="language-options"><button type="button" data-language="et" lang="et" aria-current="true">Eesti</button><button type="button" data-language="ru" lang="ru">Русский</button></div></details></nav></div></header><main id="main" class="wrap">{body}</main><footer><div class="wrap footer-grid"><div><a class="footer-brand" href="/" data-scroll-top>LAN OÜ</a><p>Работы для вашего дома в Таллинне и Харьюмаа.</p><small>Регистрационный код: 17505187</small></div><nav aria-label="Навигация в подвале">{links}</nav><div><a href="tel:+3725232477">+372 523 2477</a><a href="mailto:lebjodkin.toll68@gmail.com">lebjodkin.toll68@gmail.com</a></div></div><div class="wrap footer-bottom"><span>© <span data-current-year></span> LAN OÜ</span><a href="/" data-scroll-top>Наверх ↑</a></div></footer></body></html>'''

def local_link(match):
 url=urlsplit(match.group(1))
 if url.path not in PAGES:return match.group(0)
 target=url.path.strip('/').split('/')[-1] or 'top'
 selected=parse_qs(url.query).get('service',[''])[0]
 data=f' data-service="{escape(selected,quote=True)}"' if selected else ''
 return f'href="#{target}"'+data
# Small responsive previews are independent of the full-size viewer originals.
html=html.replace('src="/images/brand/lan-ehitus-original.jpeg?v=1"',image_sources('images/brand/lan-ehitus-original.jpeg','(max-width:700px) 158px, 165px'))
html=html.replace('src="/images/about/anatoli-portrait.png"',image_sources('images/about/anatoli-portrait.png','(max-width:700px) 68px, 82px'))
html=re.sub(r'href="(/[^" ]*)"',local_link,html)
html=html.replace('href="#top" data-scroll-top','href="/" data-scroll-top')
# Basic scraper deterrence, not a security boundary: decode only after interaction.
html=html.replace('href="tel:+3725232477"', 'href="#contact" data-contact="phone"')
html=html.replace('href="mailto:lebjodkin.toll68@gmail.com"', 'href="#contact" data-contact="email"')
html=html.replace('+372 523 2477','Позвонить').replace('lebjodkin.toll68@gmail.com','Написать email')
from i18n import load_catalog, render_page, runtime_bundle
from seo import write_crawler_files
catalog=load_catalog()
estonian=render_page(html,'et',catalog)
russian=render_page(html,'ru',catalog)
(ROOT/'ru').mkdir(exist_ok=True)
(ROOT/'ru'/'index.html').write_text(russian)
(ROOT/'website.i18n.js').write_text(runtime_bundle(catalog))
(ROOT/'index.html').write_text(estonian)
# Old bookmarks lead to the matching section, not a second copy of the site.
legacy_targets={path:('contact' if path in ('/process/','/faq/','/privacy/') else path.strip('/').split('/')[-1]) for path in PAGES if path!='/'}
# Retired services remain valid bookmarks even after their definitions disappear.
legacy_targets.update({'/services/woodwork/':'services','/services/renovation/':'services'})
for path,target in legacy_targets.items():
 redirect=f'''<!doctype html><html lang="et"><head><meta charset="utf-8"><title>LAN OÜ</title><meta name="robots" content="noindex, follow"><link rel="canonical" href="https://lanehitus.ee/"><meta http-equiv="refresh" content="0;url=/#{target}"><script>location.replace('/'+location.search+'#{target}');</script></head><body><a href="/#{target}">Mine jaotisse</a></body></html>'''
 dest=ROOT/path.strip('/')/'index.html';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(redirect)
write_crawler_files(ROOT)
print(f'Built Estonian /, Russian /ru/, robots.txt, sitemap.xml and {len(legacy_targets)} legacy redirects')
