from tau_bench.types import Task, Action

TASKS_TRAIN = [
    Task(
        annotator="synthetic",
        user_id="omar_anderson_3203",
        instruction="Your name is Omar Anderson and your zip code is 19031. You are logical, independent, relaxing, polite. Return #W6067464 via credit_card_4190576: Electric Kettle; Wall Clock; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W6067464",
                    "item_ids": ["9624127908", "8917609800"],
                    "payment_method_id": "credit_card_4190576",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sophia_nguyen_2370",
        instruction="Your name is Sophia Nguyen and your zip code is 20171. You are confident, organized. Return #W6619432 via paypal_3738584: Dumbbell Set; Yoga Mat; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W6619432",
                    "item_ids": ["3735133539", "6195938807"],
                    "payment_method_id": "paypal_3738584",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="james_li_5688",
        instruction="Your name is James Li and your email is james.li4495@example.com. You are rigid, confident, happy, curious, pessimistic. Return #W4435622 via gift_card_1725971: Water Bottle; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W4435622",
                    "item_ids": ["6777246137"],
                    "payment_method_id": "gift_card_1725971",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sofia_kovacs_7075",
        instruction="Your name is Sofia Kovacs and your zip code is 19049. You are patient, confident. For #W7736983, exchange Coffee Maker {'color': 'black', 'capacity': '4 cups', 'type': 'espresso', 'features': 'timer'} to {'color': 'stainless steel', 'type': 'drip', 'features': 'built-in grinder'}; via paypal_6840891. Cancel order #W5765741 because ordered by mistake. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W7736983",
                    "item_ids": ["5952720925"],
                    "new_item_ids": ["1323134954"],
                    "payment_method_id": "paypal_6840891",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W5765741", "reason": "ordered by mistake"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="juan_rossi_6696",
        instruction="Your name is Juan Rossi and your zip code is 77209. You are cautious, logical, organized, flexible, shy. Cancel order #W7602708 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W7602708", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="harper_thomas_9402",
        instruction="Your name is Harper Thomas and your email is harper.thomas1454@example.com. You are logical, dependent, impatient, busy. For #W7425646, change payment to credit_card_1199336. For #W7425646, modify Smart Thermostat {'compatibility': 'Apple HomeKit', 'color': 'black'} to {}; via credit_card_1283450. ",
        actions=[
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W7425646",
                    "payment_method_id": "credit_card_1199336",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W7425646",
                    "item_ids": ["4983901480"],
                    "new_item_ids": ["4983901480"],
                    "payment_method_id": "credit_card_1283450",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ava_nguyen_2175",
        instruction="Your name is Ava Nguyen and your email is ava.nguyen3664@example.com. You are outgoing, flexible, pessimistic, cautious, messy. For #W1504875, exchange Notebook {'size': 'A6', 'cover type': 'soft cover'} to {'size': 'A5'}; via paypal_6262583. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W1504875",
                    "item_ids": ["9421195098"],
                    "new_item_ids": ["9799386954"],
                    "payment_method_id": "paypal_6262583",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lucas_martin_4549",
        instruction="Your name is Lucas Martin and your email is lucas.martin5733@example.com. You are patient, cautious, organized. For #W9318778, change payment to credit_card_7862034. For #W9318778, modify Bicycle {'frame size': 'medium', 'color': 'black', 'type': 'mountain'} to {'frame size': 'large', 'color': 'red'}; Air Purifier {'room size': 'medium', 'filter type': 'HEPA', 'features': 'quiet operation'} to {}; via credit_card_7862034. ",
        actions=[
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W9318778",
                    "payment_method_id": "credit_card_7862034",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W9318778",
                    "item_ids": ["2143041831", "3076708684"],
                    "new_item_ids": ["5606522780", "3076708684"],
                    "payment_method_id": "credit_card_7862034",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lucas_muller_4380",
        instruction="Your name is Lucas Muller and your email is lucas.muller7899@example.com. You are patient, cautious. For #W3206099, modify Gaming Mouse {'color': 'black', 'sensor type': 'optical', 'connectivity': 'wired'} to {}; via gift_card_2748512. Return #W1523776 via gift_card_2748512: Smart Thermostat; ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W3206099",
                    "item_ids": ["3330317167"],
                    "new_item_ids": ["3330317167"],
                    "payment_method_id": "gift_card_2748512",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W1523776",
                    "item_ids": ["8593894906"],
                    "payment_method_id": "gift_card_2748512",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="aarav_brown_3744",
        instruction="Your name is Aarav Brown and your email is aarav.brown3708@example.com. You are busy, patient. For #W5065081, modify Water Bottle {'capacity': '750ml', 'material': 'glass', 'color': 'black'} to {'capacity': '500ml', 'material': 'stainless steel', 'color': 'green'}; via credit_card_3627996. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W5065081",
                    "item_ids": ["4579334072"],
                    "new_item_ids": ["7533802601"],
                    "payment_method_id": "credit_card_3627996",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mei_martin_4260",
        instruction="Your name is Mei Martin and your zip code is 32124. You are messy, creative, outgoing, rigid, cautious. For #W5564375, exchange LED Light Bulb {'brightness': '60W equivalent', 'color temperature': 'daylight', 'connectivity': 'none'} to {'brightness': '75W equivalent', 'connectivity': 'Wi-Fi'}; Office Chair {'material': 'fabric', 'color': 'black', 'armrest': 'none', 'backrest height': 'high-back'} to {}; via paypal_2299608. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W5564375",
                    "item_ids": ["5570660360", "1793929609"],
                    "new_item_ids": ["7445824652", "1793929609"],
                    "payment_method_id": "paypal_2299608",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yara_ito_8499",
        instruction="Your name is Yara Ito and your email is yara.ito7353@example.com. You are cautious, flexible, patient, happy. For #W8353027, exchange Grill {'type': 'electric', 'size': 'medium', 'features': 'rotisserie'} to {'type': 'charcoal', 'features': 'side burner'}; via paypal_1679017. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W8353027",
                    "item_ids": ["7717598293"],
                    "new_item_ids": ["7848293342"],
                    "payment_method_id": "paypal_1679017",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="harper_johansson_2663",
        instruction="Your name is Harper Johansson and your zip code is 80281. You are happy, direct, confident, optimistic. Cancel order #W3525030 because no longer needed. Cancel order #W3282177 because ordered by mistake. For #W2912646, change address to {'order_id': '#W2912646', 'address1': '953 Park Avenue', 'address2': 'Suite 613', 'city': 'New York', 'country': 'USA', 'state': 'NY', 'zip': '10064'} (same as #W1780552). For #W2912646, modify Sunglasses {'frame color': 'brown', 'lens color': 'brown', 'lens type': 'polarized', 'frame material': 'plastic'} to {'frame color': 'black'}; Luggage Set {'piece count': '3-piece', 'color': 'blue', 'material': 'softshell'} to {'piece count': '4-piece'}; via paypal_4820484. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W3525030", "reason": "no longer needed"},
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W3282177", "reason": "ordered by mistake"},
            ),
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W2912646",
                    "address1": "953 Park Avenue",
                    "address2": "Suite 613",
                    "city": "New York",
                    "country": "USA",
                    "state": "NY",
                    "zip": "10064",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W2912646",
                    "item_ids": ["9672174103", "6301799585"],
                    "new_item_ids": ["4358482460", "8759627937"],
                    "payment_method_id": "paypal_4820484",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="emma_kovacs_5477",
        instruction="Your name is Emma Kovacs and your email is emma.kovacs5723@example.com. You are direct, sad. Cancel order #W7109609 because ordered by mistake. Cancel order #W6554908 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W7109609", "reason": "ordered by mistake"},
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W6554908", "reason": "ordered by mistake"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="daiki_hernandez_1356",
        instruction="Your name is Daiki Hernandez and your zip code is 91203. You are sad, outgoing, messy, polite. For #W1166549, exchange Electric Kettle {'capacity': '1L', 'material': 'glass', 'color': 'white'} to {'material': 'stainless steel', 'color': 'black'}; via credit_card_1289579. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W1166549",
                    "item_ids": ["5268233322"],
                    "new_item_ids": ["7602931732"],
                    "payment_method_id": "credit_card_1289579",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_gonzalez_8900",
        instruction="Your name is Yusuf Gonzalez and your zip code is 91455. You are logical, busy, outgoing, independent, pessimistic. For #W1679211, exchange Jigsaw Puzzle {'pieces': '2000', 'theme': 'fantasy', 'difficulty level': 'beginner'} to {'pieces': '500', 'theme': 'art', 'difficulty level': 'intermediate'}; T-Shirt {'color': 'blue', 'size': 'M', 'material': 'cotton', 'style': 'crew neck'} to {'color': 'red', 'size': 'L', 'style': 'v-neck'}; via paypal_3022415. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W1679211",
                    "item_ids": ["7127170374", "9612497925"],
                    "new_item_ids": ["4068787148", "3234800602"],
                    "payment_method_id": "paypal_3022415",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_silva_7273",
        instruction="Your name is Olivia Silva and your zip code is 32240. You are creative, optimistic. Cancel order #W7613749 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W7613749", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_moore_9003",
        instruction="Your name is Ethan Moore and your email is ethan.moore4109@example.com. You are logical, independent, direct, curious, impatient. For #W6026015, exchange Luggage Set {'piece count': '2-piece', 'color': 'red', 'material': 'hardshell'} to {'material': 'softshell'}; Dumbbell Set {'weight range': '55-75 lbs', 'material': 'urethane', 'set type': 'adjustable'} to {'weight range': '30-50 lbs', 'material': 'iron', 'set type': 'fixed'}; via credit_card_6361025. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W6026015",
                    "item_ids": ["8964750292", "6130713659"],
                    "new_item_ids": ["7160999700", "3333391894"],
                    "payment_method_id": "credit_card_6361025",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mia_silva_4504",
        instruction="Your name is Mia Silva and your zip code is 95173. You are dependent, flexible. For #W6319233, exchange Bookshelf {'material': 'glass', 'color': 'black', 'height': '3 ft'} to {'color': 'brown', 'height': '5 ft'}; via credit_card_9308469. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W6319233",
                    "item_ids": ["1768466237"],
                    "new_item_ids": ["4894369688"],
                    "payment_method_id": "credit_card_9308469",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_sanchez_7289",
        instruction="Your name is Ethan Sanchez and your email is ethan.sanchez3299@example.com. You are pessimistic, shy, curious, relaxing. For #W7147989, modify Grill {'type': 'electric', 'size': 'portable', 'features': 'none'} to {'features': 'rotisserie'}; via gift_card_5917510. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W7147989",
                    "item_ids": ["1120917161"],
                    "new_item_ids": ["5745575001"],
                    "payment_method_id": "gift_card_5917510",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_lopez_6291",
        instruction="Your name is Ethan Lopez and your email is ethan.lopez8943@example.com. You are pessimistic, patient, confident, organized. For #W6426438, modify Wristwatch {'strap material': 'silicone', 'dial color': 'blue'} to {'strap material': 'leather', 'dial color': 'black'}; via gift_card_7219486. For #W6779827, modify Espresso Machine {'pressure': '19 bar', 'capacity': '2L', 'type': 'manual'} to {'pressure': '9 bar', 'capacity': '1.5L'}; via credit_card_9789590. For #W8632528, exchange Hiking Boots {'size': '10', 'material': 'leather', 'waterproof': 'no'} to {'size': '12', 'material': 'synthetic'}; via gift_card_7219486. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6426438",
                    "item_ids": ["8886009523"],
                    "new_item_ids": ["9949163720"],
                    "payment_method_id": "gift_card_7219486",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6779827",
                    "item_ids": ["3379843752"],
                    "new_item_ids": ["2190871011"],
                    "payment_method_id": "credit_card_9789590",
                },
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W8632528",
                    "item_ids": ["2185126308"],
                    "new_item_ids": ["4582956489"],
                    "payment_method_id": "gift_card_7219486",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="aarav_santos_4279",
        instruction="Your name is Aarav Santos and your email is aarav.santos2789@example.com. You are patient, pessimistic, insecure. For #W6111820, modify Wireless Earbuds {'color': 'blue', 'battery life': '4 hours', 'water resistance': 'IPX7'} to {'battery life': '8 hours', 'water resistance': 'IPX4'}; via credit_card_3816099. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6111820",
                    "item_ids": ["2757705742"],
                    "new_item_ids": ["8555936349"],
                    "payment_method_id": "credit_card_3816099",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="aarav_santos_2259",
        instruction="Your name is Aarav Santos and your email is aarav.santos8320@example.com. You are insecure, polite, happy. For #W9672333, modify Vacuum Cleaner {'type': 'canister', 'bagged/bagless': 'bagged', 'features': 'cordless'} to {}; via paypal_7664977. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W9672333",
                    "item_ids": ["1345513440"],
                    "new_item_ids": ["1345513440"],
                    "payment_method_id": "paypal_7664977",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="noah_taylor_8533",
        instruction="Your name is Noah Taylor and your zip code is 85010. You are relaxing, impatient, insecure, direct. For #W2286993, modify Skateboard {'deck material': 'bamboo', 'length': '31 inch', 'design': 'plain'} to {'deck material': 'plastic', 'design': 'custom'}; via gift_card_5354170. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W2286993",
                    "item_ids": ["4293355847"],
                    "new_item_ids": ["5038485381"],
                    "payment_method_id": "gift_card_5354170",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="juan_rossi_6696",
        instruction="Your name is Juan Rossi and your zip code is 77209. You are independent, shy, curious, relaxing. For #W7602708, change payment to gift_card_8893815. For #W7602708, modify Garden Hose {'length': '25ft', 'material': 'vinyl', 'color': 'green'} to {'color': 'blue'}; via gift_card_8893815. ",
        actions=[
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W7602708",
                    "payment_method_id": "gift_card_8893815",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W7602708",
                    "item_ids": ["3369928769"],
                    "new_item_ids": ["9829827210"],
                    "payment_method_id": "gift_card_8893815",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sophia_jackson_7119",
        instruction="Your name is Sophia Jackson and your email is sophia.jackson9875@example.com. You are pessimistic, outgoing, sad. For #W3977493, exchange Water Bottle {'capacity': '500ml', 'material': 'stainless steel', 'color': 'green'} to {'material': 'glass'}; via credit_card_6748580. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W3977493",
                    "item_ids": ["7533802601"],
                    "new_item_ids": ["5758737025"],
                    "payment_method_id": "credit_card_6748580",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="juan_lopez_5820",
        instruction="Your name is Juan Lopez and your zip code is 85060. You are organized, direct, sad, optimistic, curious. For #W3386832, change address to {'order_id': '#W3386832', 'address1': '411 Park Avenue', 'address2': 'Suite 987', 'city': 'Phoenix', 'country': 'USA', 'state': 'AZ', 'zip': '85060'} (same as #W3700848). For #W3386832, modify Cycling Helmet {'size': 'M', 'color': 'blue', 'ventilation': 'low'} to {'ventilation': 'high'}; Espresso Machine {'pressure': '9 bar', 'capacity': '2L', 'type': 'automatic'} to {'capacity': '1L', 'type': 'manual'}; Garden Hose {'length': '50ft', 'material': 'vinyl', 'color': 'green'} to {'material': 'latex', 'color': 'black'}; via paypal_6729210. ",
        actions=[
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W3386832",
                    "address1": "411 Park Avenue",
                    "address2": "Suite 987",
                    "city": "Phoenix",
                    "country": "USA",
                    "state": "AZ",
                    "zip": "85060",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W3386832",
                    "item_ids": ["3339188619", "3709608322", "8249784860"],
                    "new_item_ids": ["9013366374", "7407838442", "4024196380"],
                    "payment_method_id": "paypal_6729210",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="fatima_johnson_7581",
        instruction="Your name is Fatima Johnson and your email is fatima.johnson2300@example.com. You are creative, happy, curious, polite, impatient. For #W5199551, change payment to gift_card_1675628. For #W5199551, modify Cycling Helmet {'size': 'S', 'color': 'black', 'ventilation': 'medium'} to {'color': 'red', 'ventilation': 'low'}; Wristwatch {'strap material': 'silicone', 'dial color': 'black'} to {'strap material': 'metal', 'dial color': 'white'}; via paypal_5364164. ",
        actions=[
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W5199551",
                    "payment_method_id": "gift_card_1675628",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W5199551",
                    "item_ids": ["5537798301", "1994478369"],
                    "new_item_ids": ["3358616356", "2407258246"],
                    "payment_method_id": "paypal_5364164",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mason_kovacs_7590",
        instruction="Your name is Mason Kovacs and your zip code is 98137. You are direct, logical. For #W6030855, modify Bluetooth Speaker {'color': 'black', 'battery life': '20 hours', 'water resistance': 'no'} to {'color': 'red'}; via credit_card_4314033. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6030855",
                    "item_ids": ["5650803029"],
                    "new_item_ids": ["1052700637"],
                    "payment_method_id": "credit_card_4314033",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ava_nguyen_6646",
        instruction="Your name is Ava Nguyen and your zip code is 94128. You are logical, confident, busy. Cancel order #W1242543 because no longer needed. Cancel order #W9232383 because no longer needed. Cancel order #W8367380 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W1242543", "reason": "no longer needed"},
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W9232383", "reason": "no longer needed"},
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W8367380", "reason": "ordered by mistake"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="isabella_santos_1643",
        instruction="Your name is Isabella Santos and your email is isabella.santos9317@example.com. You are optimistic, confident, flexible. For #W9667707, change address to {'order_id': '#W9667707', 'address1': '967 Sunset Drive', 'address2': 'Suite 613', 'city': 'Fort Worth', 'country': 'USA', 'state': 'TX', 'zip': '76176'} (same as #W1654332). For #W9667707, modify Running Shoes {'size': '9', 'color': 'white', 'material': 'mesh', 'sole': 'rubber'} to {'color': 'black', 'material': 'synthetic'}; E-Reader {'screen size': '8-inch', 'connectivity': 'Wi-Fi', 'storage': '32GB'} to {'screen size': '7-inch', 'connectivity': 'Wi-Fi + Cellular'}; via credit_card_4056740. ",
        actions=[
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W9667707",
                    "address1": "967 Sunset Drive",
                    "address2": "Suite 613",
                    "city": "Fort Worth",
                    "country": "USA",
                    "state": "TX",
                    "zip": "76176",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W9667707",
                    "item_ids": ["9635758562", "7609274509"],
                    "new_item_ids": ["4107812777", "4273929280"],
                    "payment_method_id": "credit_card_4056740",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_lopez_3865",
        instruction="Your name is Olivia Lopez and your zip code is 76171. You are dependent, happy, confident, optimistic, cautious. For #W9373487, modify Portable Charger {'capacity': '20000mAh', 'output': 'Wireless', 'color': 'blue'} to {'capacity': '5000mAh', 'output': 'USB-C', 'color': 'white'}; via gift_card_7711863. For #W2692684, exchange Tablet {'screen size': '10-inch', 'storage': '128GB', 'color': 'black'} to {'screen size': '8-inch', 'color': 'gold'}; via gift_card_7711863. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W9373487",
                    "item_ids": ["4063401924"],
                    "new_item_ids": ["7866854614"],
                    "payment_method_id": "gift_card_7711863",
                },
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W2692684",
                    "item_ids": ["3788616824"],
                    "new_item_ids": ["6065192424"],
                    "payment_method_id": "gift_card_7711863",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="fatima_taylor_3452",
        instruction="Your name is Fatima Taylor and your zip code is 32169. You are rigid, curious, sad. Return #W5285031 via credit_card_7952624: Tablet; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W5285031",
                    "item_ids": ["2235648106"],
                    "payment_method_id": "credit_card_7952624",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ivan_santos_7021",
        instruction="Your name is Ivan Santos and your email is ivan.santos5925@example.com. You are happy, independent, polite, patient, busy. For #W5801125, modify Tea Kettle {'material': 'glass', 'capacity': '1.5 liters', 'stovetop compatibility': 'gas'} to {'material': 'ceramic', 'stovetop compatibility': 'induction'}; via paypal_5543657. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W5801125",
                    "item_ids": ["9647374798"],
                    "new_item_ids": ["3312883418"],
                    "payment_method_id": "paypal_5543657",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mei_silva_6882",
        instruction="Your name is Mei Silva and your zip code is 91147. You are curious, outgoing. For #W2640384, exchange Gaming Mouse {'color': 'black', 'sensor type': 'optical', 'connectivity': 'wired'} to {}; via paypal_6619428. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W2640384",
                    "item_ids": ["3330317167"],
                    "new_item_ids": ["3330317167"],
                    "payment_method_id": "paypal_6619428",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="isabella_johansson_2152",
        instruction="Your name is Isabella Johansson and your email is isabella.johansson9391@example.com. You are polite, pessimistic, organized, rigid. For #W2575533, change address to {'order_id': '#W2575533', 'address1': '812 Cedar Avenue', 'address2': 'Suite 500', 'city': 'Houston', 'country': 'USA', 'state': 'TX', 'zip': '77129'} (same as #W5565470). For #W2575533, modify E-Reader {'screen size': '8-inch', 'connectivity': 'Wi-Fi', 'storage': '8GB'} to {'screen size': '7-inch', 'connectivity': 'Wi-Fi + Cellular', 'storage': '32GB'}; Portable Charger {'capacity': '20000mAh', 'output': 'Wireless', 'color': 'black'} to {}; Garden Hose {'length': '50ft', 'material': 'vinyl', 'color': 'black'} to {'length': '25ft', 'color': 'green'}; via paypal_3024827. Return #W5565470 via paypal_3024827: Electric Kettle; Mechanical Keyboard; Pet Bed; For #W3792453, exchange Skateboard {'deck material': 'bamboo', 'length': '31 inch', 'design': 'plain'} to {'deck material': 'plastic'}; via paypal_3024827. ",
        actions=[
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W2575533",
                    "address1": "812 Cedar Avenue",
                    "address2": "Suite 500",
                    "city": "Houston",
                    "country": "USA",
                    "state": "TX",
                    "zip": "77129",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W2575533",
                    "item_ids": ["9494281769", "8349903180", "5206946487"],
                    "new_item_ids": ["4273929280", "8349903180", "3369928769"],
                    "payment_method_id": "paypal_3024827",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W5565470",
                    "item_ids": ["7602931732", "9570044148", "6857426243"],
                    "payment_method_id": "paypal_3024827",
                },
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W3792453",
                    "item_ids": ["4293355847"],
                    "new_item_ids": ["3877188862"],
                    "payment_method_id": "paypal_3024827",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mei_ahmed_4909",
        instruction="Your name is Mei Ahmed and your email is mei.ahmed4901@example.com. You are busy, impatient, organized, rigid, optimistic. For #W2598324, modify Espresso Machine {'pressure': '19 bar', 'capacity': '2L', 'type': 'manual'} to {'capacity': '1L', 'type': 'capsule'}; via credit_card_5902940. For #W3239882, exchange Tablet {'screen size': '10-inch', 'storage': '64GB', 'color': 'silver'} to {'screen size': '7-inch', 'storage': '128GB', 'color': 'black'}; via credit_card_5902940. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W2598324",
                    "item_ids": ["3379843752"],
                    "new_item_ids": ["6200867091"],
                    "payment_method_id": "credit_card_5902940",
                },
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W3239882",
                    "item_ids": ["2106335193"],
                    "new_item_ids": ["4913411651"],
                    "payment_method_id": "credit_card_5902940",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_johnson_7053",
        instruction="Your name is Ethan Johnson and your zip code is 80298. You are logical, confident, shy, organized, dependent. For #W7450915, exchange Bookshelf {'material': 'metal', 'color': 'brown', 'height': '6 ft'} to {'material': 'wood', 'height': '5 ft'}; via gift_card_6892585. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W7450915",
                    "item_ids": ["6735339143"],
                    "new_item_ids": ["2244749153"],
                    "payment_method_id": "gift_card_6892585",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="raj_lee_3061",
        instruction="Your name is Raj Lee and your zip code is 75368. You are rigid, busy, logical, confident, happy. For #W9933266, modify Pet Bed {'size': 'small', 'material': 'fleece', 'color': 'brown'} to {'size': 'medium', 'color': 'grey'}; Yoga Mat {'thickness': '4mm', 'material': 'PVC', 'color': 'blue'} to {'thickness': '6mm', 'color': 'green'}; via paypal_4133936. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W9933266",
                    "item_ids": ["4537595158", "5586947715"],
                    "new_item_ids": ["6857426243", "7510236436"],
                    "payment_method_id": "paypal_4133936",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mohamed_santos_2427",
        instruction="Your name is Mohamed Santos and your zip code is 76188. You are pessimistic, creative. For #W4840405, exchange Backpack {'color': 'green', 'size': 'small', 'material': 'polyester', 'compartment': 'laptop'} to {'color': 'black', 'size': 'large'}; via gift_card_4710915. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W4840405",
                    "item_ids": ["3557711149"],
                    "new_item_ids": ["6906307980"],
                    "payment_method_id": "gift_card_4710915",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_sanchez_2914",
        instruction="Your name is Olivia Sanchez and your email is olivia.sanchez1894@example.com. You are busy, sad. Cancel order #W5101035 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W5101035", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="fatima_wilson_6873",
        instruction="Your name is Fatima Wilson and your email is fatima.wilson5906@example.com. You are happy, impatient, messy, confident. For #W4556683, exchange Wireless Earbuds {'color': 'blue', 'battery life': '8 hours', 'water resistance': 'IPX4'} to {'battery life': '6 hours'}; Bluetooth Speaker {'color': 'blue', 'battery life': '10 hours', 'water resistance': 'yes'} to {'color': 'red', 'battery life': '20 hours'}; via credit_card_9557278. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W4556683",
                    "item_ids": ["8555936349", "4716977452"],
                    "new_item_ids": ["1646531091", "7617930199"],
                    "payment_method_id": "credit_card_9557278",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="isabella_taylor_7478",
        instruction="Your name is Isabella Taylor and your email is isabella.taylor7762@example.com. You are outgoing, organized, patient. For #W6717215, exchange Portable Charger {'capacity': '5000mAh', 'output': 'USB-C', 'color': 'white'} to {}; T-Shirt {'color': 'purple', 'size': 'XL', 'material': 'cotton', 'style': 'crew neck'} to {'color': 'red', 'size': 'L', 'style': 'v-neck'}; via gift_card_5501047. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W6717215",
                    "item_ids": ["7866854614", "8124970213"],
                    "new_item_ids": ["7866854614", "3234800602"],
                    "payment_method_id": "gift_card_5501047",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lei_ahmed_1705",
        instruction="Your name is Lei Ahmed and your email is lei.ahmed1696@example.com. You are relaxing, independent. Cancel order #W9132840 because ordered by mistake. For #W6724985, change address to {'order_id': '#W6724985', 'address1': '558 Cedar Street', 'address2': 'Suite 298', 'city': 'Houston', 'country': 'USA', 'state': 'TX', 'zip': '77158'} (same as #W9015076). For #W6724985, modify Water Bottle {'capacity': '500ml', 'material': 'stainless steel', 'color': 'green'} to {'capacity': '1000ml', 'color': 'red'}; Bookshelf {'material': 'glass', 'color': 'white', 'height': '5 ft'} to {'color': 'black', 'height': '3 ft'}; via credit_card_3593714. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W9132840", "reason": "ordered by mistake"},
            ),
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W6724985",
                    "address1": "558 Cedar Street",
                    "address2": "Suite 298",
                    "city": "Houston",
                    "country": "USA",
                    "state": "TX",
                    "zip": "77158",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6724985",
                    "item_ids": ["7533802601", "8895454203"],
                    "new_item_ids": ["2439754078", "1768466237"],
                    "payment_method_id": "credit_card_3593714",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sofia_rossi_8776",
        instruction="Your name is Sofia Rossi and your email is sofia.rossi2645@example.com. You are dependent, rigid, creative, confident, relaxing. For #W2818151, modify Luggage Set {'piece count': '4-piece', 'color': 'red', 'material': 'hardshell'} to {'piece count': '3-piece', 'color': 'blue', 'material': 'softshell'}; via credit_card_5051208. Cancel order #W5500815 because ordered by mistake. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W2818151",
                    "item_ids": ["9956648681"],
                    "new_item_ids": ["6301799585"],
                    "payment_method_id": "credit_card_5051208",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W5500815", "reason": "ordered by mistake"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yara_johansson_1629",
        instruction="Your name is Yara Johansson and your zip code is 76114. You are relaxing, optimistic, rigid, outgoing, happy. For #W9994227, exchange Cycling Helmet {'size': 'S', 'color': 'blue', 'ventilation': 'low'} to {'size': 'M', 'color': 'red', 'ventilation': 'high'}; via credit_card_4582364. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W9994227",
                    "item_ids": ["5886093635"],
                    "new_item_ids": ["8573379326"],
                    "payment_method_id": "credit_card_4582364",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lei_anderson_8271",
        instruction="Your name is Lei Anderson and your zip code is 76192. You are impatient, confident, dependent. Return #W7242815 via paypal_1808675: Tablet; For #W6002467, change address to {'order_id': '#W6002467', 'address1': '544 Sunset Drive', 'address2': 'Suite 337', 'city': 'Jacksonville', 'country': 'USA', 'state': 'FL', 'zip': '32205'} (same as #W1866533). For #W6002467, modify Cycling Helmet {'size': 'L', 'color': 'blue', 'ventilation': 'low'} to {'size': 'S'}; via paypal_1808675. ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W7242815",
                    "item_ids": ["6948061616"],
                    "payment_method_id": "paypal_1808675",
                },
            ),
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W6002467",
                    "address1": "544 Sunset Drive",
                    "address2": "Suite 337",
                    "city": "Jacksonville",
                    "country": "USA",
                    "state": "FL",
                    "zip": "32205",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6002467",
                    "item_ids": ["7907773809"],
                    "new_item_ids": ["5886093635"],
                    "payment_method_id": "paypal_1808675",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mei_kovacs_8020",
        instruction="Your name is Mei Kovacs and your email is mei.kovacs8232@example.com. You are dependent, busy, outgoing, impatient, sad. Cancel order #W7800651 because ordered by mistake. Return #W6390527 via paypal_7644869: Hiking Boots; Desk Lamp; Water Bottle; ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W7800651", "reason": "ordered by mistake"},
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W6390527",
                    "item_ids": ["1615379700", "8384507844", "8538875209"],
                    "payment_method_id": "paypal_7644869",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sophia_martin_8570",
        instruction="Your name is Sophia Martin and your email is sophia.martin4832@example.com. You are optimistic, messy, creative. For #W1092119, change address to {'order_id': '#W1092119', 'address1': '760 Elm Avenue', 'address2': 'Suite 564', 'city': 'Houston', 'country': 'USA', 'state': 'TX', 'zip': '77034'} (same as #W1603792). For #W1092119, modify Luggage Set {'piece count': '3-piece', 'color': 'silver', 'material': 'softshell'} to {'piece count': '4-piece', 'color': 'blue'}; via credit_card_5694100. ",
        actions=[
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W1092119",
                    "address1": "760 Elm Avenue",
                    "address2": "Suite 564",
                    "city": "Houston",
                    "country": "USA",
                    "state": "TX",
                    "zip": "77034",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W1092119",
                    "item_ids": ["6690069155"],
                    "new_item_ids": ["8759627937"],
                    "payment_method_id": "credit_card_5694100",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="emma_kovacs_5477",
        instruction="Your name is Emma Kovacs and your email is emma.kovacs5723@example.com. You are shy, patient, rigid, independent. Cancel order #W6554908 because ordered by mistake. Cancel order #W7109609 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W6554908", "reason": "ordered by mistake"},
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W7109609", "reason": "no longer needed"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="chen_brown_8075",
        instruction="Your name is Chen Brown and your zip code is 95190. You are impatient, logical. Cancel order #W4296426 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W4296426", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="liam_anderson_5973",
        instruction="Your name is Liam Anderson and your email is liam.anderson5932@example.com. You are patient, polite, sad. For #W1544028, exchange Jigsaw Puzzle {'pieces': '2000', 'theme': 'animals', 'difficulty level': 'intermediate'} to {'pieces': '1500', 'theme': 'art'}; Wristwatch {'strap material': 'silicone', 'dial color': 'blue'} to {'dial color': 'black'}; via credit_card_9185943. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W1544028",
                    "item_ids": ["5645314103", "8886009523"],
                    "new_item_ids": ["5546244844", "1994478369"],
                    "payment_method_id": "credit_card_9185943",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_smith_8953",
        instruction="Your name is Olivia Smith and your email is olivia.smith9157@example.com. You are organized, happy. Return #W3794101 via paypal_2076152: Cycling Helmet; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W3794101",
                    "item_ids": ["3339188619"],
                    "payment_method_id": "paypal_2076152",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="anya_brown_2024",
        instruction="Your name is Anya Brown and your email is anya.brown8893@example.com. You are insecure, shy. Cancel order #W1430028 because no longer needed. Cancel order #W1170711 because no longer needed. For #W8883368, modify Smart Watch {'color': 'black', 'band material': 'leather', 'display': 'AMOLED'} to {'color': 'silver', 'display': 'LCD'}; E-Reader {'screen size': '6-inch', 'connectivity': 'Wi-Fi', 'storage': '8GB'} to {}; via credit_card_3414703. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W1430028", "reason": "no longer needed"},
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W1170711", "reason": "no longer needed"},
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W8883368",
                    "item_ids": ["9320099340", "5510402676"],
                    "new_item_ids": ["9811090008", "5510402676"],
                    "payment_method_id": "credit_card_3414703",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="raj_moore_7909",
        instruction="Your name is Raj Moore and your zip code is 20566. You are happy, outgoing, rigid, optimistic. Return #W3467101 via gift_card_6009199: LED Light Bulb; Headphones; Smart Watch; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W3467101",
                    "item_ids": ["5111440845", "9805150490", "2860956907"],
                    "payment_method_id": "gift_card_6009199",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="raj_lopez_5873",
        instruction="Your name is Raj Lopez and your email is raj.lopez2997@example.com. You are polite, logical, dependent. Cancel order #W7162915 because ordered by mistake. For #W5107138, modify Hiking Boots {'size': '7', 'material': 'synthetic', 'waterproof': 'no'} to {}; via paypal_7007375. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W7162915", "reason": "ordered by mistake"},
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W5107138",
                    "item_ids": ["1437889264"],
                    "new_item_ids": ["1437889264"],
                    "payment_method_id": "paypal_7007375",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="aarav_lee_1982",
        instruction="Your name is Aarav Lee and your email is aarav.lee6460@example.com. You are optimistic, happy, independent, patient. For #W3586556, modify Tablet {'screen size': '8-inch', 'storage': '128GB', 'color': 'gold'} to {'screen size': '7-inch', 'color': 'black'}; via credit_card_1640996. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W3586556",
                    "item_ids": ["6065192424"],
                    "new_item_ids": ["4913411651"],
                    "payment_method_id": "credit_card_1640996",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="amelia_silva_7726",
        instruction="Your name is Amelia Silva and your zip code is 19117. You are cautious, independent, patient. Cancel order #W4836353 because no longer needed. For #W7773202, exchange Hiking Boots {'size': '12', 'material': 'leather', 'waterproof': 'yes'} to {'size': '7'}; via gift_card_3491931. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W4836353", "reason": "no longer needed"},
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W7773202",
                    "item_ids": ["8277474082"],
                    "new_item_ids": ["3812493782"],
                    "payment_method_id": "gift_card_3491931",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ava_nguyen_6971",
        instruction="Your name is Ava Nguyen and your email is ava.nguyen1860@example.com. You are confident, cautious, direct, messy. Return #W7597893 via gift_card_8640626: Smart Thermostat; Mechanical Keyboard; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W7597893",
                    "item_ids": ["9480266227", "9991484137"],
                    "payment_method_id": "gift_card_8640626",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="anya_patel_3710",
        instruction="Your name is Anya Patel and your email is anya.patel9309@example.com. You are direct, sad, curious, logical, patient. For #W6131421, exchange Makeup Kit {'skin tone': 'light', 'kit size': 'professional', 'brand': 'Brand A'} to {'skin tone': 'dark', 'brand': 'Brand B'}; via credit_card_4142574. Return #W6174054 via gift_card_6566420: Fleece Jacket; Vacuum Cleaner; Dumbbell Set; ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W6131421",
                    "item_ids": ["6509212169"],
                    "new_item_ids": ["5012998807"],
                    "payment_method_id": "credit_card_4142574",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W6174054",
                    "item_ids": ["8590708195", "9970989750", "6130713659"],
                    "payment_method_id": "gift_card_6566420",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="raj_li_9474",
        instruction="Your name is Raj Li and your zip code is 76184. You are direct, impatient, insecure, busy. Cancel order #W8967935 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W8967935", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sophia_garcia_1101",
        instruction="Your name is Sophia Garcia and your email is sophia.garcia9791@example.com. You are patient, messy. Return #W8727985 via gift_card_9450778: Jigsaw Puzzle; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W8727985",
                    "item_ids": ["9030221155"],
                    "payment_method_id": "gift_card_9450778",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_thomas_1791",
        instruction="Your name is Ethan Thomas and your email is ethan.thomas7730@example.com. You are patient, relaxing, rigid, logical, messy. For #W8465042, modify Smartphone {'color': 'gold', 'storage': '128GB', 'RAM': '4GB', 'screen size': '5.8-inch'} to {'color': 'black', 'RAM': '8GB'}; Smart Watch {'color': 'black', 'band material': 'silicone', 'display': 'AMOLED'} to {'color': 'gold'}; via paypal_6982172. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W8465042",
                    "item_ids": ["9929635042", "4920090458"],
                    "new_item_ids": ["1507389580", "2681513500"],
                    "payment_method_id": "paypal_6982172",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mei_kovacs_8020",
        instruction="Your name is Mei Kovacs and your zip code is 28236. You are dependent, rigid, relaxing. For #W7800651, modify Gaming Mouse {'color': 'RGB', 'sensor type': 'optical', 'connectivity': 'wired'} to {'color': 'black', 'sensor type': 'laser'}; via paypal_7644869. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W7800651",
                    "item_ids": ["5796612084"],
                    "new_item_ids": ["2193628750"],
                    "payment_method_id": "paypal_7644869",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sofia_li_3261",
        instruction="Your name is Sofia Li and your zip code is 10199. You are flexible, outgoing, dependent, impatient, messy. For #W6874763, exchange Fleece Jacket {'size': 'L', 'color': 'black', 'zipper': 'full'} to {}; Digital Camera {'resolution': '20MP', 'zoom': '10x', 'storage': 'CF card'} to {'zoom': '5x'}; via credit_card_4046723. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W6874763",
                    "item_ids": ["9385662952", "7583936705"],
                    "new_item_ids": ["9385662952", "9644439410"],
                    "payment_method_id": "credit_card_4046723",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ava_nguyen_4072",
        instruction="Your name is Ava Nguyen and your zip code is 28251. You are patient, curious, messy, confident, polite. Cancel order #W8732376 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W8732376", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_garcia_1208",
        instruction="Your name is Olivia Garcia and your email is olivia.garcia2695@example.com. You are pessimistic, messy, outgoing. For #W1075114, exchange Wireless Earbuds {'color': 'blue', 'battery life': '4 hours', 'water resistance': 'IPX7'} to {'battery life': '8 hours', 'water resistance': 'IPX4'}; via gift_card_5115976. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W1075114",
                    "item_ids": ["2757705742"],
                    "new_item_ids": ["8555936349"],
                    "payment_method_id": "gift_card_5115976",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sofia_ito_5484",
        instruction="Your name is Sofia Ito and your zip code is 19169. You are relaxing, confident, rigid. Return #W5257743 via paypal_6882355: T-Shirt; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W5257743",
                    "item_ids": ["9647292434"],
                    "payment_method_id": "paypal_6882355",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mia_jackson_2250",
        instruction="Your name is Mia Jackson and your email is mia.jackson5798@example.com. You are patient, insecure, shy, curious, logical. Cancel order #W6236251 because ordered by mistake. Cancel order #W2618034 because ordered by mistake. For #W1205816, change address to {'order_id': '#W1205816', 'address1': '629 Sunset Drive', 'address2': 'Suite 581', 'city': 'San Diego', 'country': 'USA', 'state': 'CA', 'zip': '92159'} (same as #W6236251). For #W1205816, change payment to gift_card_5715854. For #W1205816, modify Tea Kettle {'material': 'ceramic', 'capacity': '1.5 liters', 'stovetop compatibility': 'induction'} to {'material': 'glass', 'capacity': '2 liters'}; via gift_card_5715854. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W6236251", "reason": "ordered by mistake"},
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W2618034", "reason": "ordered by mistake"},
            ),
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W1205816",
                    "address1": "629 Sunset Drive",
                    "address2": "Suite 581",
                    "city": "San Diego",
                    "country": "USA",
                    "state": "CA",
                    "zip": "92159",
                },
            ),
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W1205816",
                    "payment_method_id": "gift_card_5715854",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W1205816",
                    "item_ids": ["3312883418"],
                    "new_item_ids": ["7292993796"],
                    "payment_method_id": "gift_card_5715854",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lucas_brown_6720",
        instruction="Your name is Lucas Brown and your email is lucas.brown9344@example.com. You are creative, cautious, happy. Cancel order #W4860251 because ordered by mistake. For #W6239298, exchange Bookshelf {'material': 'glass', 'color': 'black', 'height': '5 ft'} to {'material': 'wood', 'color': 'brown', 'height': '6 ft'}; Water Bottle {'capacity': '1000ml', 'material': 'stainless steel', 'color': 'blue'} to {'capacity': '750ml', 'material': 'plastic', 'color': 'black'}; E-Reader {'screen size': '8-inch', 'connectivity': 'Wi-Fi', 'storage': '8GB'} to {'screen size': '7-inch', 'connectivity': 'Wi-Fi + Cellular', 'storage': '32GB'}; via credit_card_2112420. For #W9218746, exchange Backpack {'color': 'black', 'size': 'small', 'material': 'nylon', 'compartment': 'laptop'} to {'color': 'grey', 'size': 'large', 'material': 'polyester', 'compartment': 'hydration'}; Vacuum Cleaner {'type': 'canister', 'bagged/bagless': 'bagged', 'features': 'pet hair removal'} to {'type': 'robotic', 'features': 'cordless'}; via credit_card_2112420. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W4860251", "reason": "ordered by mistake"},
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W6239298",
                    "item_ids": ["4900661478", "2366567022", "9494281769"],
                    "new_item_ids": ["7154215719", "7199146548", "4273929280"],
                    "payment_method_id": "credit_card_2112420",
                },
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W9218746",
                    "item_ids": ["7824298782", "2872451762"],
                    "new_item_ids": ["6309044598", "4602305039"],
                    "payment_method_id": "credit_card_2112420",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="omar_kim_3528",
        instruction="Your name is Omar Kim and your zip code is 32214. You are sad, relaxing, curious, creative, polite. Cancel order #W7111824 because no longer needed. For #W8557584, change payment to credit_card_3577130. For #W8557584, modify Tea Kettle {'material': 'glass', 'capacity': '1 liter', 'stovetop compatibility': 'electric'} to {'capacity': '2 liters', 'stovetop compatibility': 'induction'}; Jigsaw Puzzle {'pieces': '500', 'theme': 'art', 'difficulty level': 'beginner'} to {}; via credit_card_3577130. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W7111824", "reason": "no longer needed"},
            ),
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W8557584",
                    "payment_method_id": "credit_card_3577130",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W8557584",
                    "item_ids": ["9747045638", "1096508426"],
                    "new_item_ids": ["7292993796", "1096508426"],
                    "payment_method_id": "credit_card_3577130",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mei_martin_4260",
        instruction="Your name is Mei Martin and your zip code is 32124. You are curious, creative, patient, relaxing, polite. Return #W5564375 via paypal_2299608: Digital Camera; Running Shoes; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W5564375",
                    "item_ids": ["7583936705", "1775591963"],
                    "payment_method_id": "paypal_2299608",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="emma_nguyen_6662",
        instruction="Your name is Emma Nguyen and your email is emma.nguyen8892@example.com. You are rigid, optimistic, impatient, relaxing, organized. For #W2092674, exchange Wristwatch {'strap material': 'metal', 'dial color': 'black'} to {'strap material': 'leather', 'dial color': 'white'}; via paypal_2499655. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W2092674",
                    "item_ids": ["4510078629"],
                    "new_item_ids": ["1355937109"],
                    "payment_method_id": "paypal_2499655",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="emma_kovacs_9839",
        instruction="Your name is Emma Kovacs and your zip code is 32190. You are dependent, relaxing, curious. For #W8661412, modify Office Chair {'material': 'fabric', 'color': 'black', 'armrest': 'fixed', 'backrest height': 'standard'} to {'color': 'gray', 'armrest': 'none', 'backrest height': 'high-back'}; Water Bottle {'capacity': '500ml', 'material': 'stainless steel', 'color': 'black'} to {'capacity': '750ml', 'material': 'plastic'}; via credit_card_7239357. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W8661412",
                    "item_ids": ["8426249116", "3453331371"],
                    "new_item_ids": ["9459890810", "7199146548"],
                    "payment_method_id": "credit_card_7239357",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="james_li_5688",
        instruction="Your name is James Li and your zip code is 10083. You are insecure, organized, relaxing, sad. For #W3638028, exchange Jigsaw Puzzle {'pieces': '1000', 'theme': 'animals', 'difficulty level': 'expert'} to {'pieces': '500', 'theme': 'art', 'difficulty level': 'beginner'}; Indoor Security Camera {'resolution': '4K', 'field of view': '130 degrees', 'connectivity': 'Wi-Fi'} to {'resolution': '2K', 'connectivity': 'Ethernet'}; via gift_card_1725971. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W3638028",
                    "item_ids": ["4572024853", "5810561222"],
                    "new_item_ids": ["1096508426", "8470360507"],
                    "payment_method_id": "gift_card_1725971",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="evelyn_davis_7541",
        instruction="Your name is Evelyn Davis and your zip code is 32136. You are confident, sad. Return #W6798117 via paypal_9734841: Wall Clock; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W6798117",
                    "item_ids": ["6508153405"],
                    "payment_method_id": "paypal_9734841",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_taylor_7149",
        instruction="Your name is Yusuf Taylor and your zip code is 95154. You are rigid, confident, independent, cautious, direct. For #W2702727, modify Yoga Mat {'thickness': '6mm', 'material': 'natural rubber', 'color': 'pink'} to {'material': 'PVC', 'color': 'green'}; via credit_card_3599838. For #W8268610, change address to {'order_id': '#W8268610', 'address1': '227 Oak Street', 'address2': 'Suite 699', 'city': 'Washington', 'country': 'USA', 'state': 'DC', 'zip': '20564'} (same as #W5690487). For #W8268610, modify Desk Lamp {'color': 'white', 'brightness': 'high', 'power source': 'USB'} to {'color': 'silver', 'brightness': 'low', 'power source': 'AC adapter'}; via credit_card_3599838. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W2702727",
                    "item_ids": ["2733768059"],
                    "new_item_ids": ["7510236436"],
                    "payment_method_id": "credit_card_3599838",
                },
            ),
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W8268610",
                    "address1": "227 Oak Street",
                    "address2": "Suite 699",
                    "city": "Washington",
                    "country": "USA",
                    "state": "DC",
                    "zip": "20564",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W8268610",
                    "item_ids": ["9083642334"],
                    "new_item_ids": ["1569765161"],
                    "payment_method_id": "credit_card_3599838",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ava_moore_4814",
        instruction="Your name is Ava Moore and your email is ava.moore2450@example.com. You are patient, organized, outgoing, happy, direct. Cancel order #W8331214 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W8331214", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="isabella_santos_1643",
        instruction="Your name is Isabella Santos and your zip code is 10020. You are flexible, creative, pessimistic. Cancel order #W9527030 because no longer needed. Return #W1654332 via credit_card_4056740: Mechanical Keyboard; ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W9527030", "reason": "no longer needed"},
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W1654332",
                    "item_ids": ["9665000388"],
                    "payment_method_id": "credit_card_4056740",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mei_li_2872",
        instruction="Your name is Mei Li and your zip code is 92149. You are sad, flexible, relaxing. For #W2936099, exchange Wireless Earbuds {'color': 'blue', 'battery life': '4 hours', 'water resistance': 'IPX7'} to {'color': 'white', 'water resistance': 'not resistant'}; Bookshelf {'material': 'glass', 'color': 'black', 'height': '3 ft'} to {'color': 'white', 'height': '5 ft'}; via paypal_4060450. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W2936099",
                    "item_ids": ["2757705742", "1768466237"],
                    "new_item_ids": ["2052249669", "8895454203"],
                    "payment_method_id": "paypal_4060450",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_ito_3591",
        instruction="Your name is Olivia Ito and your email is olivia.ito5204@example.com. You are dependent, organized, insecure. For #W5442520, modify Patio Umbrella {'size': '7 ft', 'color': 'red', 'material': 'polyester', 'tilt mechanism': 'manual tilt'} to {'size': '6 ft', 'color': 'blue', 'material': 'sunbrella', 'tilt mechanism': 'auto tilt'}; Hiking Boots {'size': '8', 'material': 'leather', 'waterproof': 'yes'} to {'size': '11'}; via gift_card_7794233. For #W3657213, change payment to credit_card_9753331. For #W3657213, modify Digital Camera {'resolution': '24MP', 'zoom': '3x', 'storage': 'SD card'} to {'resolution': '30MP'}; via paypal_8049766. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W5442520",
                    "item_ids": ["3111466194", "2648909398"],
                    "new_item_ids": ["2001307871", "6159919747"],
                    "payment_method_id": "gift_card_7794233",
                },
            ),
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W3657213",
                    "payment_method_id": "credit_card_9753331",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W3657213",
                    "item_ids": ["5996159312"],
                    "new_item_ids": ["1804581713"],
                    "payment_method_id": "paypal_8049766",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_sanchez_7289",
        instruction="Your name is Ethan Sanchez and your email is ethan.sanchez3299@example.com. You are optimistic, messy, confident, cautious, impatient. For #W7147989, change address to {'order_id': '#W7147989', 'address1': '386 Cedar Avenue', 'address2': 'Suite 683', 'city': 'Columbus', 'country': 'USA', 'state': 'OH', 'zip': '43119'} (same as #W5560533). For #W7147989, modify Grill {'type': 'electric', 'size': 'portable', 'features': 'none'} to {'features': 'rotisserie'}; Office Chair {'material': 'leather', 'color': 'red', 'armrest': 'none', 'backrest height': 'high-back'} to {'material': 'mesh', 'color': 'gray', 'armrest': 'fixed'}; via gift_card_5917510. ",
        actions=[
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W7147989",
                    "address1": "386 Cedar Avenue",
                    "address2": "Suite 683",
                    "city": "Columbus",
                    "country": "USA",
                    "state": "OH",
                    "zip": "43119",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W7147989",
                    "item_ids": ["1120917161", "3609437808"],
                    "new_item_ids": ["5745575001", "2386562819"],
                    "payment_method_id": "gift_card_5917510",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mei_martin_4260",
        instruction="Your name is Mei Martin and your zip code is 32124. You are busy, rigid, insecure. For #W7017301, modify Bicycle {'frame size': 'large', 'color': 'red', 'type': 'mountain'} to {'frame size': 'medium', 'color': 'black'}; via paypal_2299608. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W7017301",
                    "item_ids": ["5606522780"],
                    "new_item_ids": ["2143041831"],
                    "payment_method_id": "paypal_2299608",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mei_ahmed_4909",
        instruction="Your name is Mei Ahmed and your email is mei.ahmed4901@example.com. You are flexible, messy, curious, direct, dependent. For #W3239882, exchange Makeup Kit {'skin tone': 'light', 'kit size': 'professional', 'brand': 'Brand A'} to {'skin tone': 'dark', 'brand': 'Brand C'}; via credit_card_5902940. For #W7553978, exchange Skateboard {'deck material': 'plastic', 'length': '34 inch', 'design': 'plain'} to {'deck material': 'bamboo', 'length': '28 inch'}; via credit_card_5902940. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W3239882",
                    "item_ids": ["6509212169"],
                    "new_item_ids": ["1763705424"],
                    "payment_method_id": "credit_card_5902940",
                },
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W7553978",
                    "item_ids": ["3098764622"],
                    "new_item_ids": ["8176740019"],
                    "payment_method_id": "credit_card_5902940",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="chen_silva_7485",
        instruction="Your name is Chen Silva and your email is chen.silva2698@example.com. You are optimistic, rigid, happy, busy, impatient. Return #W9571698 via gift_card_7250692: Pet Bed; Tablet; Return #W3069600 via credit_card_1565124: Makeup Kit; Skateboard; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W9571698",
                    "item_ids": ["7381052709", "6065192424"],
                    "payment_method_id": "gift_card_7250692",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W3069600",
                    "item_ids": ["5012998807", "4545791457"],
                    "payment_method_id": "credit_card_1565124",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lei_khan_6353",
        instruction="Your name is Lei Khan and your zip code is 92182. You are impatient, shy. For #W2787996, exchange T-Shirt {'color': 'red', 'size': 'XXL', 'material': 'cotton', 'style': 'crew neck'} to {'color': 'purple', 'size': 'S', 'material': 'polyester', 'style': 'v-neck'}; via gift_card_6786837. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W2787996",
                    "item_ids": ["9354168549"],
                    "new_item_ids": ["9647292434"],
                    "payment_method_id": "gift_card_6786837",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sofia_ahmed_9514",
        instruction="Your name is Sofia Ahmed and your zip code is 90819. You are rigid, polite, confident. For #W2002395, exchange Garden Hose {'length': '25ft', 'material': 'vinyl', 'color': 'green'} to {'length': '100ft', 'material': 'latex', 'color': 'blue'}; Smart Thermostat {'compatibility': 'Apple HomeKit', 'color': 'white'} to {'color': 'stainless steel'}; via gift_card_6117300. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W2002395",
                    "item_ids": ["3369928769", "3377900078"],
                    "new_item_ids": ["8481719475", "9480266227"],
                    "payment_method_id": "gift_card_6117300",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mohamed_lee_5442",
        instruction="Your name is Mohamed Lee and your email is mohamed.lee1888@example.com. You are sad, optimistic. Cancel order #W6302827 because ordered by mistake. For #W6114312, exchange Dumbbell Set {'weight range': '30-50 lbs', 'material': 'rubber', 'set type': 'adjustable'} to {'weight range': '5-25 lbs', 'material': 'urethane', 'set type': 'fixed'}; via credit_card_8169552. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W6302827", "reason": "ordered by mistake"},
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W6114312",
                    "item_ids": ["3735133539"],
                    "new_item_ids": ["6585768447"],
                    "payment_method_id": "credit_card_8169552",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_jackson_7865",
        instruction="Your name is Yusuf Jackson and your email is yusuf.jackson4654@example.com. You are confident, creative. Cancel order #W2087737 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W2087737", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="isabella_lopez_6490",
        instruction="Your name is Isabella Lopez and your email is isabella.lopez3271@example.com. You are curious, polite, shy. Cancel order #W4923227 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W4923227", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mei_kovacs_5767",
        instruction="Your name is Mei Kovacs and your email is mei.kovacs4296@example.com. You are shy, pessimistic, messy, impatient. Cancel order #W8193638 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W8193638", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="omar_khan_2363",
        instruction="Your name is Omar Khan and your zip code is 75203. You are independent, outgoing, sad. For #W2421430, exchange Fleece Jacket {'size': 'S', 'color': 'red', 'zipper': 'half'} to {'size': 'XL', 'color': 'navy'}; Yoga Mat {'thickness': '6mm', 'material': 'natural rubber', 'color': 'pink'} to {'thickness': '5mm', 'material': 'TPE'}; Action Camera {'resolution': '1080p', 'waterproof': 'no', 'color': 'silver'} to {'resolution': '5K', 'color': 'black'}; via credit_card_4420174. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W2421430",
                    "item_ids": ["5992316252", "2733768059", "1810466394"],
                    "new_item_ids": ["8590708195", "1794273251", "7523669277"],
                    "payment_method_id": "credit_card_4420174",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_muller_6097",
        instruction="Your name is Ethan Muller and your email is ethan.muller6617@example.com. You are optimistic, polite, rigid. For #W3155037, exchange Smartphone {'color': 'rose gold', 'storage': '64GB', 'RAM': '8GB', 'screen size': '6.1-inch'} to {'color': 'black', 'storage': '128GB', 'screen size': '5.8-inch'}; via credit_card_5721095. For #W4683557, modify Water Bottle {'capacity': '500ml', 'material': 'stainless steel', 'color': 'green'} to {'capacity': '1000ml', 'color': 'black'}; Vacuum Cleaner {'type': 'upright', 'bagged/bagless': 'bagged', 'features': 'pet hair removal'} to {'type': 'canister'}; via credit_card_5721095. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W3155037",
                    "item_ids": ["3952176596"],
                    "new_item_ids": ["1507389580"],
                    "payment_method_id": "credit_card_5721095",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W4683557",
                    "item_ids": ["7533802601", "3526747930"],
                    "new_item_ids": ["7661609223", "2872451762"],
                    "payment_method_id": "credit_card_5721095",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="omar_muller_7891",
        instruction="Your name is Omar Muller and your email is omar.muller4197@example.com. You are impatient, dependent, logical. Return #W6573840 via gift_card_3689412: Electric Kettle; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W6573840",
                    "item_ids": ["4458619711"],
                    "payment_method_id": "gift_card_3689412",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="evelyn_patel_8882",
        instruction="Your name is Evelyn Patel and your email is evelyn.patel2010@example.com. You are direct, insecure, logical, dependent. Return #W9158156 via paypal_3704667: Bluetooth Speaker; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W9158156",
                    "item_ids": ["7751905257"],
                    "payment_method_id": "paypal_3704667",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_johnson_7053",
        instruction="Your name is Ethan Johnson and your email is ethan.johnson2557@example.com. You are shy, rigid, dependent. Return #W5321777 via gift_card_6892585: Espresso Machine; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W5321777",
                    "item_ids": ["7441167885"],
                    "payment_method_id": "gift_card_6892585",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_khan_7091",
        instruction="Your name is Yusuf Khan and your email is yusuf.khan7390@example.com. You are curious, relaxing, shy, insecure. Cancel order #W3579467 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W3579467", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mei_davis_8935",
        instruction="Your name is Mei Davis and your email is mei.davis6811@example.com. You are busy, cautious, rigid, direct, optimistic. For #W1267569, modify Gaming Mouse {'color': 'white', 'sensor type': 'laser', 'connectivity': 'wireless'} to {'sensor type': 'optical'}; via credit_card_1061405. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W1267569",
                    "item_ids": ["7420906769"],
                    "new_item_ids": ["8896479688"],
                    "payment_method_id": "credit_card_1061405",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_jackson_1219",
        instruction="Your name is Olivia Jackson and your email is olivia.jackson2465@example.com. You are logical, dependent, pessimistic, impatient. For #W6975922, modify Jigsaw Puzzle {'pieces': '2000', 'theme': 'animals', 'difficulty level': 'intermediate'} to {'pieces': '1000', 'difficulty level': 'expert'}; via paypal_3999493. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6975922",
                    "item_ids": ["5645314103"],
                    "new_item_ids": ["4572024853"],
                    "payment_method_id": "paypal_3999493",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="noah_sanchez_2690",
        instruction="Your name is Noah Sanchez and your zip code is 20056. You are polite, curious. For #W8645374, change address to {'order_id': '#W8645374', 'address1': '297 Highland Drive', 'address2': 'Suite 550', 'city': 'Washington', 'country': 'USA', 'state': 'DC', 'zip': '20056'} (same as #W4864669). For #W8645374, modify Digital Camera {'resolution': '20MP', 'zoom': '5x', 'storage': 'CF card'} to {'resolution': '30MP', 'zoom': '3x', 'storage': 'SD card'}; via gift_card_9909795. Return #W7293142 via gift_card_9909795: Wireless Earbuds; Hiking Boots; Skateboard; ",
        actions=[
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W8645374",
                    "address1": "297 Highland Drive",
                    "address2": "Suite 550",
                    "city": "Washington",
                    "country": "USA",
                    "state": "DC",
                    "zip": "20056",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W8645374",
                    "item_ids": ["9644439410"],
                    "new_item_ids": ["1804581713"],
                    "payment_method_id": "gift_card_9909795",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W7293142",
                    "item_ids": ["3694871183", "2185126308", "6956751343"],
                    "payment_method_id": "gift_card_9909795",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_garcia_1670",
        instruction="Your name is Yusuf Garcia and your zip code is 46202. You are curious, outgoing, busy. Cancel order #W7639559 because no longer needed. Cancel order #W3691773 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W7639559", "reason": "no longer needed"},
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W3691773", "reason": "no longer needed"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_garcia_4691",
        instruction="Your name is Olivia Garcia and your email is olivia.garcia6676@example.com. You are creative, flexible, shy, sad, polite. For #W3279695, modify Indoor Security Camera {'resolution': '2K', 'field of view': '130 degrees', 'connectivity': 'Ethernet'} to {'resolution': '4K'}; via gift_card_4584785. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W3279695",
                    "item_ids": ["8470360507"],
                    "new_item_ids": ["6901578702"],
                    "payment_method_id": "gift_card_4584785",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="noah_sanchez_2690",
        instruction="Your name is Noah Sanchez and your email is noah.sanchez7461@example.com. You are logical, polite, impatient, busy. Return #W4864669 via gift_card_9909795: Wireless Earbuds {'color': 'black', 'battery life': '6 hours', 'water resistance': 'IPX7'}; Wireless Earbuds {'color': 'black', 'battery life': '4 hours', 'water resistance': 'IPX7'}; Digital Camera; For #W7293142, exchange Skateboard {'deck material': 'bamboo', 'length': '34 inch', 'design': 'custom'} to {'length': '31 inch', 'design': 'plain'}; Mechanical Keyboard {'switch type': 'clicky', 'backlight': 'RGB', 'size': 'full size'} to {'backlight': 'none', 'size': '80%'}; via gift_card_9909795. ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W4864669",
                    "item_ids": ["5565631513", "9580569596", "9228757377"],
                    "payment_method_id": "gift_card_9909795",
                },
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W7293142",
                    "item_ids": ["6956751343", "9025753381"],
                    "new_item_ids": ["4293355847", "9665000388"],
                    "payment_method_id": "gift_card_9909795",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="anya_sanchez_9707",
        instruction="Your name is Anya Sanchez and your zip code is 43171. You are messy, busy, outgoing. Return #W4442043 via paypal_1191071: Cycling Helmet; Bicycle; Smartphone; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W4442043",
                    "item_ids": ["6697922351", "7758198585", "3187628796"],
                    "payment_method_id": "paypal_1191071",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="fatima_anderson_7445",
        instruction="Your name is Fatima Anderson and your email is fatima.anderson1082@example.com. You are impatient, sad, rigid, pessimistic. Return #W1842597 via gift_card_8070316: Running Shoes; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W1842597",
                    "item_ids": ["9791469541"],
                    "payment_method_id": "gift_card_8070316",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mia_davis_8827",
        instruction="Your name is Mia Davis and your zip code is 28229. You are shy, confident, curious, impatient. Cancel order #W6577842 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W6577842", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="amelia_gonzalez_4098",
        instruction="Your name is Amelia Gonzalez and your email is amelia.gonzalez4271@example.com. You are rigid, busy, patient, pessimistic. Return #W7209932 via gift_card_2611937: Backpack; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W7209932",
                    "item_ids": ["5917587651"],
                    "payment_method_id": "gift_card_2611937",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_thomas_1791",
        instruction="Your name is Ethan Thomas and your zip code is 43188. You are direct, insecure. Return #W7764382 via paypal_6982172: Laptop; Pet Bed; Mechanical Keyboard; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W7764382",
                    "item_ids": ["3334537816", "5067898160", "9665000388"],
                    "payment_method_id": "paypal_6982172",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lei_anderson_8271",
        instruction="Your name is Lei Anderson and your zip code is 76192. You are direct, rigid, optimistic, insecure. Return #W4072946 via paypal_1808675: Hiking Boots; Action Camera; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W4072946",
                    "item_ids": ["8106223139", "5436236388"],
                    "payment_method_id": "paypal_1808675",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="noah_ito_3850",
        instruction="Your name is Noah Ito and your email is noah.ito4296@example.com. You are logical, cautious, organized, sad. For #W6729841, change address to {'order_id': '#W6729841', 'address1': '144 Lakeview Drive', 'address2': 'Suite 925', 'city': 'New York', 'country': 'USA', 'state': 'NY', 'zip': '10228'} (same as #W3445693). For #W6729841, modify Bluetooth Speaker {'color': 'black', 'battery life': '10 hours', 'water resistance': 'yes'} to {'color': 'red', 'battery life': '20 hours', 'water resistance': 'no'}; via credit_card_1620755. ",
        actions=[
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W6729841",
                    "address1": "144 Lakeview Drive",
                    "address2": "Suite 925",
                    "city": "New York",
                    "country": "USA",
                    "state": "NY",
                    "zip": "10228",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6729841",
                    "item_ids": ["5855700373"],
                    "new_item_ids": ["1052700637"],
                    "payment_method_id": "credit_card_1620755",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="aarav_gonzalez_5113",
        instruction="Your name is Aarav Gonzalez and your email is aarav.gonzalez9269@example.com. You are rigid, confident, messy. For #W6797115, exchange Air Purifier {'room size': 'large', 'filter type': 'HEPA', 'features': 'night mode'} to {'room size': 'medium', 'filter type': 'carbon', 'features': 'quiet operation'}; via paypal_6121064. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W6797115",
                    "item_ids": ["8302289002"],
                    "new_item_ids": ["9375701158"],
                    "payment_method_id": "paypal_6121064",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_moore_3587",
        instruction="Your name is Ethan Moore and your email is ethan.moore4935@example.com. You are patient, sad, flexible. For #W6353188, exchange Perfume {'scent family': 'woody', 'size': '30ml', 'gender': 'men'} to {'gender': 'women'}; via credit_card_6173085. For #W7156413, exchange Luggage Set {'piece count': '3-piece', 'color': 'silver', 'material': 'softshell'} to {'color': 'blue'}; Bluetooth Speaker {'color': 'red', 'battery life': '10 hours', 'water resistance': 'no'} to {'battery life': '20 hours', 'water resistance': 'yes'}; via credit_card_6173085. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W6353188",
                    "item_ids": ["5081446110"],
                    "new_item_ids": ["8316205423"],
                    "payment_method_id": "credit_card_6173085",
                },
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W7156413",
                    "item_ids": ["6690069155", "1689914594"],
                    "new_item_ids": ["6301799585", "7617930199"],
                    "payment_method_id": "credit_card_6173085",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="liam_anderson_5973",
        instruction="Your name is Liam Anderson and your email is liam.anderson5932@example.com. You are shy, cautious. For #W2119065, exchange Patio Umbrella {'size': '6 ft', 'color': 'red', 'material': 'olefin', 'tilt mechanism': 'manual tilt'} to {'color': 'green', 'tilt mechanism': 'auto tilt'}; via credit_card_9185943. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W2119065",
                    "item_ids": ["8170914468"],
                    "new_item_ids": ["9879255677"],
                    "payment_method_id": "credit_card_9185943",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="aarav_santos_2259",
        instruction="Your name is Aarav Santos and your email is aarav.santos8320@example.com. You are relaxing, dependent, curious, creative. Cancel order #W9672333 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W9672333", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lei_hernandez_8500",
        instruction="Your name is Lei Hernandez and your email is lei.hernandez7247@example.com. You are organized, busy, polite, optimistic, sad. For #W2982823, exchange Cycling Helmet {'size': 'M', 'color': 'red', 'ventilation': 'medium'} to {'size': 'S', 'ventilation': 'low'}; via gift_card_5245016. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W2982823",
                    "item_ids": ["1719127154"],
                    "new_item_ids": ["3358616356"],
                    "payment_method_id": "gift_card_5245016",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_garcia_1670",
        instruction="Your name is Yusuf Garcia and your zip code is 46202. You are sad, dependent. For #W3691773, modify Water Bottle {'capacity': '500ml', 'material': 'stainless steel', 'color': 'green'} to {'capacity': '750ml', 'color': 'red'}; via gift_card_4303603. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W3691773",
                    "item_ids": ["7533802601"],
                    "new_item_ids": ["6777246137"],
                    "payment_method_id": "gift_card_4303603",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="aarav_davis_4756",
        instruction="Your name is Aarav Davis and your zip code is 76150. You are insecure, flexible, sad, organized. Return #W3223435 via gift_card_9708163: Electric Kettle; T-Shirt; Garden Hose; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W3223435",
                    "item_ids": ["3015420423", "3799046073", "3230708338"],
                    "payment_method_id": "gift_card_9708163",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yara_ito_8499",
        instruction="Your name is Yara Ito and your email is yara.ito7353@example.com. You are organized, happy, dependent, polite, insecure. For #W1809337, exchange Makeup Kit {'skin tone': 'medium', 'kit size': 'professional', 'brand': 'Brand A'} to {'kit size': 'basic', 'brand': 'Brand C'}; Cycling Helmet {'size': 'M', 'color': 'blue', 'ventilation': 'low'} to {'size': 'S', 'color': 'white', 'ventilation': 'medium'}; Tea Kettle {'material': 'stainless steel', 'capacity': '2 liters', 'stovetop compatibility': 'gas'} to {'material': 'glass', 'capacity': '1 liter'}; via paypal_1679017. Return #W8353027 via paypal_1679017: Electric Kettle; ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W1809337",
                    "item_ids": ["2882812427", "3339188619", "4238115171"],
                    "new_item_ids": ["3017803871", "7811981098", "3909406921"],
                    "payment_method_id": "paypal_1679017",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W8353027",
                    "item_ids": ["9335834276"],
                    "payment_method_id": "paypal_1679017",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lei_patel_5376",
        instruction="Your name is Lei Patel and your email is lei.patel3765@example.com. You are curious, relaxing, insecure. For #W4172216, modify Dumbbell Set {'weight range': '30-50 lbs', 'material': 'rubber', 'set type': 'fixed'} to {'set type': 'adjustable'}; Electric Toothbrush {'color': 'black', 'speed settings': 'high', 'battery type': 'AA batteries'} to {'color': 'white'}; via credit_card_6450011. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W4172216",
                    "item_ids": ["6171242004", "8798690242"],
                    "new_item_ids": ["3735133539", "2645006275"],
                    "payment_method_id": "credit_card_6450011",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_ito_3591",
        instruction="Your name is Olivia Ito and your zip code is 80218. You are polite, relaxing, curious, sad. For #W7941031, modify Wristwatch {'strap material': 'leather', 'dial color': 'white'} to {'dial color': 'black'}; via paypal_8049766. For #W3657213, modify Action Camera {'resolution': '4K', 'waterproof': 'yes', 'color': 'black'} to {'resolution': '1080p'}; via gift_card_7794233. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W7941031",
                    "item_ids": ["1355937109"],
                    "new_item_ids": ["9949163720"],
                    "payment_method_id": "paypal_8049766",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W3657213",
                    "item_ids": ["6700049080"],
                    "new_item_ids": ["5925362855"],
                    "payment_method_id": "gift_card_7794233",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="harper_kovacs_8617",
        instruction="Your name is Harper Kovacs and your zip code is 95154. You are sad, busy, confident. For #W9093821, modify Wall Clock {'diameter': '10 inches', 'color': 'white', 'type': 'digital'} to {'color': 'black'}; via credit_card_7422485. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W9093821",
                    "item_ids": ["8917609800"],
                    "new_item_ids": ["8610532516"],
                    "payment_method_id": "credit_card_7422485",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="aarav_gonzalez_5113",
        instruction="Your name is Aarav Gonzalez and your email is aarav.gonzalez9269@example.com. You are impatient, rigid. For #W6797115, exchange Air Purifier {'room size': 'large', 'filter type': 'HEPA', 'features': 'night mode'} to {'filter type': 'ionic', 'features': 'smart sensors'}; via gift_card_5979071. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W6797115",
                    "item_ids": ["8302289002"],
                    "new_item_ids": ["9534205511"],
                    "payment_method_id": "gift_card_5979071",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_davis_3316",
        instruction="Your name is Olivia Davis and your zip code is 77244. You are rigid, shy, insecure. For #W7623533, exchange Jigsaw Puzzle {'pieces': '1000', 'theme': 'animals', 'difficulty level': 'beginner'} to {'pieces': '2000', 'difficulty level': 'intermediate'}; via credit_card_8278346. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W7623533",
                    "item_ids": ["4772738468"],
                    "new_item_ids": ["5645314103"],
                    "payment_method_id": "credit_card_8278346",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="noah_martin_5764",
        instruction="Your name is Noah Martin and your email is noah.martin8712@example.com. You are organized, impatient. Cancel order #W7594624 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W7594624", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sophia_garcia_1101",
        instruction="Your name is Sophia Garcia and your zip code is 78263. You are messy, busy, outgoing. For #W8727985, exchange Jigsaw Puzzle {'pieces': '2000', 'theme': 'art', 'difficulty level': 'beginner'} to {'pieces': '500', 'difficulty level': 'intermediate'}; via gift_card_9450778. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W8727985",
                    "item_ids": ["9030221155"],
                    "new_item_ids": ["4068787148"],
                    "payment_method_id": "gift_card_9450778",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="evelyn_kovacs_6742",
        instruction="Your name is Evelyn Kovacs and your email is evelyn.kovacs5369@example.com. You are independent, happy, cautious, organized. Cancel order #W6689278 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W6689278", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="daiki_silva_5033",
        instruction="Your name is Daiki Silva and your zip code is 28268. You are happy, shy, independent, curious. For #W1579160, modify Tea Kettle {'material': 'glass', 'capacity': '1 liter', 'stovetop compatibility': 'gas'} to {'capacity': '2 liters', 'stovetop compatibility': 'induction'}; Electric Kettle {'capacity': '1.5L', 'material': 'glass', 'color': 'white'} to {'capacity': '2L'}; Vacuum Cleaner {'type': 'upright', 'bagged/bagless': 'bagless', 'features': 'HEPA filter'} to {'type': 'canister', 'bagged/bagless': 'bagged', 'features': 'pet hair removal'}; via paypal_2233507. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W1579160",
                    "item_ids": ["3909406921", "9472539378", "7407609582"],
                    "new_item_ids": ["7292993796", "4064702754", "2872451762"],
                    "payment_method_id": "paypal_2233507",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lei_anderson_8271",
        instruction="Your name is Lei Anderson and your zip code is 76192. You are creative, direct, pessimistic, patient, happy. Return #W4072946 via paypal_1808675: Hiking Boots; For #W6002467, change address to {'order_id': '#W6002467', 'address1': '544 Sunset Drive', 'address2': 'Suite 337', 'city': 'Jacksonville', 'country': 'USA', 'state': 'FL', 'zip': '32205'} (same as #W1866533). For #W6002467, modify Cycling Helmet {'size': 'L', 'color': 'blue', 'ventilation': 'low'} to {'color': 'white', 'ventilation': 'medium'}; Water Bottle {'capacity': '750ml', 'material': 'stainless steel', 'color': 'blue'} to {'capacity': '1000ml', 'color': 'red'}; via paypal_1808675. ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W4072946",
                    "item_ids": ["8106223139"],
                    "payment_method_id": "paypal_1808675",
                },
            ),
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W6002467",
                    "address1": "544 Sunset Drive",
                    "address2": "Suite 337",
                    "city": "Jacksonville",
                    "country": "USA",
                    "state": "FL",
                    "zip": "32205",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6002467",
                    "item_ids": ["7907773809", "7843064651"],
                    "new_item_ids": ["6697922351", "2439754078"],
                    "payment_method_id": "paypal_1808675",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_smith_5265",
        instruction="Your name is Olivia Smith and your zip code is 80216. You are flexible, relaxing, insecure, patient, direct. Return #W5220869 via credit_card_7971769: Tea Kettle; Backpack; Desk Lamp; Return #W5202795 via credit_card_7971769: Office Chair; Action Camera; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W5220869",
                    "item_ids": ["8293778132", "6906307980", "9190635437"],
                    "payment_method_id": "credit_card_7971769",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W5202795",
                    "item_ids": ["8426249116", "4859937227"],
                    "payment_method_id": "credit_card_7971769",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lei_ahmed_1705",
        instruction="Your name is Lei Ahmed and your email is lei.ahmed1696@example.com. You are creative, happy, organized. Cancel order #W9132840 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W9132840", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="evelyn_ahmed_3960",
        instruction="Your name is Evelyn Ahmed and your email is evelyn.ahmed2006@example.com. You are creative, sad, patient, polite, organized. For #W3746173, change address to {'order_id': '#W3746173', 'address1': '137 Willow Lane', 'address2': 'Suite 127', 'city': 'Charlotte', 'country': 'USA', 'state': 'NC', 'zip': '28249'} (same as #W1416704). For #W3746173, change payment to credit_card_7898168. For #W3746173, modify Makeup Kit {'skin tone': 'medium', 'kit size': 'professional', 'brand': 'Brand A'} to {}; via credit_card_7898168. Cancel order #W1416704 because ordered by mistake. ",
        actions=[
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W3746173",
                    "address1": "137 Willow Lane",
                    "address2": "Suite 127",
                    "city": "Charlotte",
                    "country": "USA",
                    "state": "NC",
                    "zip": "28249",
                },
            ),
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W3746173",
                    "payment_method_id": "credit_card_7898168",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W3746173",
                    "item_ids": ["2882812427"],
                    "new_item_ids": ["2882812427"],
                    "payment_method_id": "credit_card_7898168",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W1416704", "reason": "ordered by mistake"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="isabella_sanchez_2068",
        instruction="Your name is Isabella Sanchez and your zip code is 85093. You are relaxing, logical, shy. For #W4386313, change address to {'order_id': '#W4386313', 'address1': '964 Sunset Drive', 'address2': 'Suite 782', 'city': 'New York', 'country': 'USA', 'state': 'NY', 'zip': '10199'} (same as #W1713682). For #W4386313, modify Skateboard {'deck material': 'bamboo', 'length': '28 inch', 'design': 'plain'} to {'length': '34 inch', 'design': 'graphic'}; via paypal_8516781. ",
        actions=[
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W4386313",
                    "address1": "964 Sunset Drive",
                    "address2": "Suite 782",
                    "city": "New York",
                    "country": "USA",
                    "state": "NY",
                    "zip": "10199",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W4386313",
                    "item_ids": ["8176740019"],
                    "new_item_ids": ["3541421151"],
                    "payment_method_id": "paypal_8516781",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mei_wilson_1792",
        instruction="Your name is Mei Wilson and your email is mei.wilson5728@example.com. You are cautious, organized, polite, optimistic, busy. Cancel order #W4498118 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W4498118", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mason_lopez_8519",
        instruction="Your name is Mason Lopez and your email is mason.lopez8921@example.com. You are independent, happy, optimistic, messy. For #W9892169, modify Cycling Helmet {'size': 'M', 'color': 'red', 'ventilation': 'low'} to {'size': 'L', 'color': 'black', 'ventilation': 'high'}; via credit_card_2327218. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W9892169",
                    "item_ids": ["6401214406"],
                    "new_item_ids": ["1665571435"],
                    "payment_method_id": "credit_card_2327218",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="noah_sanchez_2690",
        instruction="Your name is Noah Sanchez and your email is noah.sanchez7461@example.com. You are pessimistic, shy, happy, creative, messy. For #W7293142, exchange Mechanical Keyboard {'switch type': 'clicky', 'backlight': 'RGB', 'size': 'full size'} to {'switch type': 'linear', 'size': '80%'}; via gift_card_9909795. Cancel order #W8645374 because no longer needed. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W7293142",
                    "item_ids": ["9025753381"],
                    "new_item_ids": ["8484921793"],
                    "payment_method_id": "gift_card_9909795",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W8645374", "reason": "no longer needed"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sofia_lee_8857",
        instruction="Your name is Sofia Lee and your email is sofia.lee5283@example.com. You are organized, happy, curious, polite, insecure. Return #W4143549 via paypal_3572679: Indoor Security Camera; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W4143549",
                    "item_ids": ["6867855179"],
                    "payment_method_id": "paypal_3572679",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="harper_thomas_9402",
        instruction="Your name is Harper Thomas and your email is harper.thomas1454@example.com. You are pessimistic, creative, messy, shy, dependent. For #W7425646, modify Yoga Mat {'thickness': '6mm', 'material': 'PVC', 'color': 'green'} to {'thickness': '4mm', 'color': 'blue'}; Smart Thermostat {'compatibility': 'Apple HomeKit', 'color': 'black'} to {}; via credit_card_1283450. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W7425646",
                    "item_ids": ["7510236436", "4983901480"],
                    "new_item_ids": ["5586947715", "4983901480"],
                    "payment_method_id": "credit_card_1283450",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_smith_7905",
        instruction="Your name is Ethan Smith and your email is ethan.smith4017@example.com. You are cautious, messy, confident, busy, logical. Cancel order #W1138897 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W1138897", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="evelyn_gonzalez_8209",
        instruction="Your name is Evelyn Gonzalez and your email is evelyn.gonzalez7152@example.com. You are insecure, flexible, polite. For #W4500945, exchange Gaming Mouse {'color': 'black', 'sensor type': 'optical', 'connectivity': 'wired'} to {'sensor type': 'laser', 'connectivity': 'wireless'}; via paypal_6069934. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W4500945",
                    "item_ids": ["3330317167"],
                    "new_item_ids": ["8214883393"],
                    "payment_method_id": "paypal_6069934",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="evelyn_kovacs_6742",
        instruction="Your name is Evelyn Kovacs and your email is evelyn.kovacs5369@example.com. You are rigid, sad, shy, independent. For #W9651773, modify Digital Camera {'resolution': '20MP', 'zoom': '5x', 'storage': 'CF card'} to {'zoom': '3x', 'storage': 'SD card'}; via paypal_7732922. Return #W2768683 via paypal_7732922: Espresso Machine; Bookshelf; Digital Camera; For #W6689278, change address to {'order_id': '#W6689278', 'address1': '505 Cedar Avenue', 'address2': 'Suite 539', 'city': 'Jacksonville', 'country': 'USA', 'state': 'FL', 'zip': '32117'} (same as #W5694685). For #W6689278, modify Electric Kettle {'capacity': '1L', 'material': 'plastic', 'color': 'white'} to {'capacity': '1.5L', 'material': 'glass'}; via paypal_7732922. Cancel order #W5694685 because ordered by mistake. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W9651773",
                    "item_ids": ["9644439410"],
                    "new_item_ids": ["8363011723"],
                    "payment_method_id": "paypal_7732922",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W2768683",
                    "item_ids": ["6242772310", "8649999816", "7583936705"],
                    "payment_method_id": "paypal_7732922",
                },
            ),
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W6689278",
                    "address1": "505 Cedar Avenue",
                    "address2": "Suite 539",
                    "city": "Jacksonville",
                    "country": "USA",
                    "state": "FL",
                    "zip": "32117",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6689278",
                    "item_ids": ["2243454707"],
                    "new_item_ids": ["9472539378"],
                    "payment_method_id": "paypal_7732922",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W5694685", "reason": "ordered by mistake"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lei_anderson_8271",
        instruction="Your name is Lei Anderson and your zip code is 76192. You are happy, independent, optimistic, direct, rigid. For #W7242815, exchange Tablet {'screen size': '10-inch', 'storage': '128GB', 'color': 'gold'} to {'screen size': '7-inch', 'storage': '32GB', 'color': 'silver'}; via paypal_1808675. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W7242815",
                    "item_ids": ["6948061616"],
                    "new_item_ids": ["4615543240"],
                    "payment_method_id": "paypal_1808675",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_ahmed_6778",
        instruction="Your name is Olivia Ahmed and your zip code is 94152. You are confident, messy. For #W3972714, exchange Hiking Boots {'size': '9', 'material': 'synthetic', 'waterproof': 'yes'} to {'size': '7', 'material': 'leather'}; via credit_card_9698900. For #W2609687, modify Pet Bed {'size': 'small', 'material': 'polyester', 'color': 'brown'} to {'size': 'large', 'material': 'memory foam', 'color': 'beige'}; via gift_card_1044904. Return #W1579621 via credit_card_9698900: Water Bottle; Portable Charger; Pet Bed; Headphones; ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W3972714",
                    "item_ids": ["2658930189"],
                    "new_item_ids": ["3812493782"],
                    "payment_method_id": "credit_card_9698900",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W2609687",
                    "item_ids": ["8056198669"],
                    "new_item_ids": ["6942241102"],
                    "payment_method_id": "gift_card_1044904",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W1579621",
                    "item_ids": [
                        "4579334072",
                        "7866854614",
                        "4982943126",
                        "7184044281",
                    ],
                    "payment_method_id": "credit_card_9698900",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lei_wilson_4541",
        instruction="Your name is Lei Wilson and your zip code is 32255. You are confident, shy, patient, creative, sad. For #W2905754, exchange Garden Hose {'length': '50ft', 'material': 'vinyl', 'color': 'black'} to {}; via credit_card_3677959. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W2905754",
                    "item_ids": ["5206946487"],
                    "new_item_ids": ["5206946487"],
                    "payment_method_id": "credit_card_3677959",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="omar_silva_7446",
        instruction="Your name is Omar Silva and your email is omar.silva4147@example.com. You are relaxing, sad, optimistic. Cancel order #W9673784 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W9673784", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_smith_9087",
        instruction="Your name is Ethan Smith and your zip code is 10280. You are messy, polite, shy. For #W6711349, modify Portable Charger {'capacity': '5000mAh', 'output': 'USB-A', 'color': 'white'} to {'capacity': '20000mAh', 'output': 'USB-C'}; Digital Camera {'resolution': '24MP', 'zoom': '5x', 'storage': 'CF card'} to {'resolution': '30MP', 'zoom': '10x', 'storage': 'SD card'}; Electric Toothbrush {'color': 'white', 'speed settings': 'low', 'battery type': 'rechargeable'} to {}; via paypal_3296755. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6711349",
                    "item_ids": ["7903094618", "4326528037", "6164262152"],
                    "new_item_ids": ["1178356107", "9228757377", "6164262152"],
                    "payment_method_id": "paypal_3296755",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_hernandez_5066",
        instruction="Your name is Olivia Hernandez and your email is olivia.hernandez9440@example.com. You are cautious, relaxing, flexible. For #W5671546, exchange Garden Hose {'length': '25ft', 'material': 'latex', 'color': 'green'} to {}; via credit_card_2583849. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W5671546",
                    "item_ids": ["3230708338"],
                    "new_item_ids": ["3230708338"],
                    "payment_method_id": "credit_card_2583849",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_gonzalez_8900",
        instruction="Your name is Yusuf Gonzalez and your email is yusuf.gonzalez2399@example.com. You are outgoing, sad, flexible, cautious, pessimistic. For #W2806889, change payment to paypal_3022415. For #W2806889, modify Tea Kettle {'material': 'ceramic', 'capacity': '1.5 liters', 'stovetop compatibility': 'gas'} to {'material': 'stainless steel', 'stovetop compatibility': 'induction'}; Smartphone {'color': 'black', 'storage': '128GB', 'RAM': '4GB', 'screen size': '6.5-inch'} to {'RAM': '8GB', 'screen size': '5.8-inch'}; via paypal_3022415. For #W2230795, change payment to credit_card_7918119. For #W2230795, modify Tablet {'screen size': '10-inch', 'storage': '128GB', 'color': 'gold'} to {'storage': '64GB', 'color': 'silver'}; via credit_card_7918119. ",
        actions=[
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W2806889",
                    "payment_method_id": "paypal_3022415",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W2806889",
                    "item_ids": ["7497340597", "5339029584"],
                    "new_item_ids": ["3738831434", "1507389580"],
                    "payment_method_id": "paypal_3022415",
                },
            ),
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W2230795",
                    "payment_method_id": "credit_card_7918119",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W2230795",
                    "item_ids": ["6948061616"],
                    "new_item_ids": ["2106335193"],
                    "payment_method_id": "credit_card_7918119",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="evelyn_hernandez_1701",
        instruction="Your name is Evelyn Hernandez and your zip code is 92139. You are rigid, insecure, pessimistic, outgoing, impatient. For #W3482034, modify Grill {'type': 'electric', 'size': 'medium', 'features': 'side burner'} to {'type': 'charcoal'}; via credit_card_3631888. Return #W9628587 via credit_card_3631888: Sunglasses; Dumbbell Set; ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W3482034",
                    "item_ids": ["5666020311"],
                    "new_item_ids": ["7848293342"],
                    "payment_method_id": "credit_card_3631888",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W9628587",
                    "item_ids": ["9045948550", "8140269513"],
                    "payment_method_id": "credit_card_3631888",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ivan_hernandez_6923",
        instruction="Your name is Ivan Hernandez and your email is ivan.hernandez1120@example.com. You are flexible, patient, outgoing, messy, insecure. For #W4284542, change address to {'order_id': '#W4284542', 'address1': '894 Hickory Lane', 'address2': 'Suite 665', 'city': 'San Diego', 'country': 'USA', 'state': 'CA', 'zip': '92133'} (same as #W5838674). For #W4284542, change payment to gift_card_9368765. For #W4284542, modify Air Purifier {'room size': 'large', 'filter type': 'HEPA', 'features': 'night mode'} to {'room size': 'medium', 'filter type': 'carbon', 'features': 'quiet operation'}; Bluetooth Speaker {'color': 'red', 'battery life': '10 hours', 'water resistance': 'no'} to {'color': 'blue', 'water resistance': 'yes'}; via gift_card_9368765. ",
        actions=[
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W4284542",
                    "address1": "894 Hickory Lane",
                    "address2": "Suite 665",
                    "city": "San Diego",
                    "country": "USA",
                    "state": "CA",
                    "zip": "92133",
                },
            ),
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W4284542",
                    "payment_method_id": "gift_card_9368765",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W4284542",
                    "item_ids": ["8302289002", "1689914594"],
                    "new_item_ids": ["9375701158", "4716977452"],
                    "payment_method_id": "gift_card_9368765",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="evelyn_lopez_5487",
        instruction="Your name is Evelyn Lopez and your email is evelyn.lopez6910@example.com. You are organized, sad, confident. For #W3007862, modify Grill {'type': 'electric', 'size': 'medium', 'features': 'side burner'} to {'type': 'gas', 'size': 'portable'}; via credit_card_3566337. Cancel order #W1890669 because ordered by mistake. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W3007862",
                    "item_ids": ["5666020311"],
                    "new_item_ids": ["9724317332"],
                    "payment_method_id": "credit_card_3566337",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W1890669", "reason": "ordered by mistake"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="harper_santos_8115",
        instruction="Your name is Harper Santos and your zip code is 46237. You are direct, independent, happy, messy, busy. For #W4941028, change payment to credit_card_7507679. For #W4941028, modify Backpack {'color': 'grey', 'size': 'large', 'material': 'nylon', 'compartment': 'hydration'} to {'color': 'green', 'size': 'small', 'material': 'polyester', 'compartment': 'laptop'}; Laptop {'screen size': '17-inch', 'processor': 'i9', 'ram': '8GB', 'storage': '256GB SSD', 'color': 'silver'} to {'screen size': '15-inch', 'processor': 'i5', 'ram': '32GB', 'color': 'space grey'}; Smart Thermostat {'compatibility': 'Apple HomeKit', 'color': 'stainless steel'} to {}; via credit_card_7507679. ",
        actions=[
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W4941028",
                    "payment_method_id": "credit_card_7507679",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W4941028",
                    "item_ids": ["5726859009", "3265035808", "9480266227"],
                    "new_item_ids": ["3557711149", "2216662955", "9480266227"],
                    "payment_method_id": "credit_card_7507679",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sofia_li_3261",
        instruction="Your name is Sofia Li and your zip code is 10199. You are optimistic, outgoing, logical, messy, direct. Return #W6874763 via credit_card_4046723: E-Reader; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W6874763",
                    "item_ids": ["9494281769"],
                    "payment_method_id": "credit_card_4046723",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yara_silva_7567",
        instruction="Your name is Yara Silva and your email is yara.silva2443@example.com. You are dependent, confident, optimistic. For #W9810810, modify Bookshelf {'material': 'metal', 'color': 'black', 'height': '6 ft'} to {'material': 'wood', 'color': 'brown', 'height': '5 ft'}; Electric Kettle {'capacity': '1.5L', 'material': 'plastic', 'color': 'white'} to {'color': 'black'}; via gift_card_7252880. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W9810810",
                    "item_ids": ["3778705663", "2698416822"],
                    "new_item_ids": ["2244749153", "5428723833"],
                    "payment_method_id": "gift_card_7252880",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sophia_patel_6833",
        instruction="Your name is Sophia Patel and your email is sophia.patel9841@example.com. You are organized, optimistic, confident. Return #W2923184 via credit_card_6419343: Wireless Earbuds; Laptop; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W2923184",
                    "item_ids": ["2757705742", "1684786391"],
                    "payment_method_id": "credit_card_6419343",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="emma_kovacs_5477",
        instruction="Your name is Emma Kovacs and your email is emma.kovacs5723@example.com. You are direct, happy, rigid. For #W7109609, modify Headphones {'type': 'on-ear', 'connectivity': 'wireless', 'color': 'white'} to {'type': 'over-ear', 'color': 'black'}; Vacuum Cleaner {'type': 'robotic', 'bagged/bagless': 'bagless', 'features': 'cordless'} to {}; via gift_card_9246707. For #W6554908, modify Perfume {'scent family': 'fresh', 'size': '30ml', 'gender': 'men'} to {'scent family': 'oriental'}; via gift_card_9246707. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W7109609",
                    "item_ids": ["9805150490", "4806644905"],
                    "new_item_ids": ["7493556126", "4806644905"],
                    "payment_method_id": "gift_card_9246707",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6554908",
                    "item_ids": ["9447903288"],
                    "new_item_ids": ["1325156478"],
                    "payment_method_id": "gift_card_9246707",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ava_moore_2033",
        instruction="Your name is Ava Moore and your zip code is 78234. You are busy, creative, messy, sad. Return #W8951014 via gift_card_8168843: Backpack {'color': 'black', 'size': 'small', 'material': 'nylon', 'compartment': 'laptop'}; Bookshelf; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W8951014",
                    "item_ids": ["7824298782", "2244749153"],
                    "payment_method_id": "gift_card_8168843",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="evelyn_ahmed_3960",
        instruction="Your name is Evelyn Ahmed and your email is evelyn.ahmed2006@example.com. You are patient, rigid, busy. Cancel order #W3746173 because no longer needed. Cancel order #W1416704 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W3746173", "reason": "no longer needed"},
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W1416704", "reason": "ordered by mistake"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="anya_lee_8315",
        instruction="Your name is Anya Lee and your email is anya.lee3013@example.com. You are busy, direct, happy, organized, outgoing. For #W1335809, exchange Hiking Boots {'size': '10', 'material': 'leather', 'waterproof': 'no'} to {'size': '9', 'waterproof': 'yes'}; via paypal_3728317. For #W3176007, modify Water Bottle {'capacity': '750ml', 'material': 'stainless steel', 'color': 'blue'} to {'capacity': '500ml', 'color': 'green'}; via paypal_3728317. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W1335809",
                    "item_ids": ["2185126308"],
                    "new_item_ids": ["8106223139"],
                    "payment_method_id": "paypal_3728317",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W3176007",
                    "item_ids": ["7843064651"],
                    "new_item_ids": ["7533802601"],
                    "payment_method_id": "paypal_3728317",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="raj_santos_9079",
        instruction="Your name is Raj Santos and your zip code is 98157. You are organized, optimistic, dependent. Return #W1630030 via paypal_2417743: Electric Kettle; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W1630030",
                    "item_ids": ["4458619711"],
                    "payment_method_id": "paypal_2417743",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="fatima_nguyen_7539",
        instruction="Your name is Fatima Nguyen and your zip code is 43211. You are happy, cautious, pessimistic, impatient, creative. Cancel order #W8808563 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W8808563", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="daiki_johnson_9523",
        instruction="Your name is Daiki Johnson and your zip code is 80273. You are optimistic, relaxing, rigid, dependent, direct. Cancel order #W5282037 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W5282037", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="omar_silva_9907",
        instruction="Your name is Omar Silva and your zip code is 98141. You are polite, happy, shy, dependent, patient. For #W6151519, modify Mechanical Keyboard {'switch type': 'tactile', 'backlight': 'none', 'size': '80%'} to {'switch type': 'clicky'}; Electric Kettle {'capacity': '1L', 'material': 'plastic', 'color': 'silver'} to {'capacity': '2L', 'material': 'glass', 'color': 'white'}; Running Shoes {'size': '9', 'color': 'black', 'material': 'synthetic', 'sole': 'rubber'} to {'color': 'white', 'material': 'mesh'}; via gift_card_5193172. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6151519",
                    "item_ids": ["7658724607", "9132333852", "4107812777"],
                    "new_item_ids": ["9665000388", "4064702754", "9635758562"],
                    "payment_method_id": "gift_card_5193172",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="raj_anderson_3167",
        instruction="Your name is Raj Anderson and your email is raj.anderson6756@example.com. You are polite, outgoing, impatient. For #W6378322, exchange Smart Thermostat {'compatibility': 'Apple HomeKit', 'color': 'white'} to {'color': 'stainless steel'}; via gift_card_6662365. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W6378322",
                    "item_ids": ["3377900078"],
                    "new_item_ids": ["9480266227"],
                    "payment_method_id": "gift_card_6662365",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="anya_lee_8315",
        instruction="Your name is Anya Lee and your zip code is 78227. You are relaxing, messy, polite, happy. For #W2989580, modify Fleece Jacket {'size': 'L', 'color': 'black', 'zipper': 'full'} to {'size': 'XL', 'color': 'navy'}; via paypal_3728317. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W2989580",
                    "item_ids": ["9385662952"],
                    "new_item_ids": ["7528037711"],
                    "payment_method_id": "paypal_3728317",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="amelia_wilson_4614",
        instruction="Your name is Amelia Wilson and your zip code is 75215. You are optimistic, rigid, shy. For #W9077205, exchange Dumbbell Set {'weight range': '5-25 lbs', 'material': 'iron', 'set type': 'adjustable'} to {'weight range': '55-75 lbs', 'set type': 'fixed'}; via gift_card_7108145. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W9077205",
                    "item_ids": ["3877338112"],
                    "new_item_ids": ["2444431651"],
                    "payment_method_id": "gift_card_7108145",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yara_muller_8652",
        instruction="Your name is Yara Muller and your zip code is 85041. You are creative, relaxing, rigid, curious. Cancel order #W5995614 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W5995614", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="anya_brown_2024",
        instruction="Your name is Anya Brown and your email is anya.brown8893@example.com. You are patient, insecure. Cancel order #W1170711 because ordered by mistake. For #W1430028, change payment to credit_card_3414703. For #W1430028, change address to {'order_id': '#W1430028', 'address1': '419 Main Street', 'address2': 'Suite 730', 'city': 'Dallas', 'country': 'USA', 'state': 'TX', 'zip': '75380'} (same as #W8883368). For #W1430028, modify Running Shoes {'size': '9', 'color': 'black', 'material': 'synthetic', 'sole': 'rubber'} to {'color': 'yellow'}; via credit_card_3414703. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W1170711", "reason": "ordered by mistake"},
            ),
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W1430028",
                    "payment_method_id": "credit_card_3414703",
                },
            ),
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W1430028",
                    "address1": "419 Main Street",
                    "address2": "Suite 730",
                    "city": "Dallas",
                    "country": "USA",
                    "state": "TX",
                    "zip": "75380",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W1430028",
                    "item_ids": ["4107812777"],
                    "new_item_ids": ["9791469541"],
                    "payment_method_id": "credit_card_3414703",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yara_sanchez_9145",
        instruction="Your name is Yara Sanchez and your zip code is 43097. You are relaxing, optimistic, happy, cautious, insecure. For #W6519831, exchange Dumbbell Set {'weight range': '30-50 lbs', 'material': 'iron', 'set type': 'adjustable'} to {'weight range': '5-25 lbs', 'material': 'rubber'}; Bicycle {'frame size': 'medium', 'color': 'blue', 'type': 'road'} to {'color': 'green'}; via credit_card_5353742. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W6519831",
                    "item_ids": ["6245231688", "3624655057"],
                    "new_item_ids": ["7896397433", "7758198585"],
                    "payment_method_id": "credit_card_5353742",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lei_anderson_8271",
        instruction="Your name is Lei Anderson and your zip code is 76192. You are polite, patient. Cancel order #W6002467 because ordered by mistake. Return #W4072946 via paypal_1808675: Action Camera; Hiking Boots; ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W6002467", "reason": "ordered by mistake"},
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W4072946",
                    "item_ids": ["5436236388", "8106223139"],
                    "payment_method_id": "paypal_1808675",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="harper_ito_4653",
        instruction="Your name is Harper Ito and your email is harper.ito2682@example.com. You are insecure, patient, organized, pessimistic, relaxing. For #W5673917, exchange Tablet {'screen size': '10-inch', 'storage': '64GB', 'color': 'silver'} to {'storage': '32GB', 'color': 'black'}; via paypal_1053133. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W5673917",
                    "item_ids": ["2106335193"],
                    "new_item_ids": ["2235648106"],
                    "payment_method_id": "paypal_1053133",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sofia_li_9219",
        instruction="Your name is Sofia Li and your email is sofia.li7352@example.com. You are curious, shy, logical, organized. Cancel order #W8855135 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W8855135", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mason_johansson_2485",
        instruction="Your name is Mason Johansson and your email is mason.johansson9528@example.com. You are sad, cautious, direct, logical. Cancel order #W3358610 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W3358610", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="raj_lopez_5873",
        instruction="Your name is Raj Lopez and your email is raj.lopez2997@example.com. You are rigid, optimistic, confident. Cancel order #W3502364 because ordered by mistake. Cancel order #W7162915 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W3502364", "reason": "ordered by mistake"},
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W7162915", "reason": "no longer needed"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="emma_kovacs_9839",
        instruction="Your name is Emma Kovacs and your email is emma.kovacs2974@example.com. You are pessimistic, impatient, sad, flexible, outgoing. For #W8661412, modify Water Bottle {'capacity': '500ml', 'material': 'stainless steel', 'color': 'black'} to {'capacity': '750ml', 'color': 'red'}; via credit_card_7239357. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W8661412",
                    "item_ids": ["3453331371"],
                    "new_item_ids": ["6777246137"],
                    "payment_method_id": "credit_card_7239357",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="isabella_brown_3584",
        instruction="Your name is Isabella Brown and your email is isabella.brown8771@example.com. You are outgoing, dependent, rigid, curious. For #W7752779, exchange Jigsaw Puzzle {'pieces': '500', 'theme': 'art', 'difficulty level': 'intermediate'} to {'pieces': '1000', 'theme': 'fantasy'}; via paypal_2143483. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W7752779",
                    "item_ids": ["4068787148"],
                    "new_item_ids": ["3112842858"],
                    "payment_method_id": "paypal_2143483",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="evelyn_ahmed_3960",
        instruction="Your name is Evelyn Ahmed and your zip code is 80256. You are dependent, flexible, optimistic. Cancel order #W1416704 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W1416704", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_lopez_6291",
        instruction="Your name is Ethan Lopez and your zip code is 43275. You are cautious, messy, creative, direct. For #W8632528, exchange Hiking Boots {'size': '10', 'material': 'leather', 'waterproof': 'no'} to {'size': '9', 'waterproof': 'yes'}; via credit_card_9789590. For #W8073920, modify Hiking Boots {'size': '12', 'material': 'leather', 'waterproof': 'yes'} to {'size': '11'}; Smartphone {'color': 'gold', 'storage': '128GB', 'RAM': '4GB', 'screen size': '5.8-inch'} to {'color': 'black', 'RAM': '8GB'}; Cycling Helmet {'size': 'S', 'color': 'blue', 'ventilation': 'low'} to {'size': 'M', 'color': 'red', 'ventilation': 'high'}; via gift_card_7219486. Cancel order #W6779827 because ordered by mistake. For #W6426438, modify Skateboard {'deck material': 'plastic', 'length': '28 inch', 'design': 'custom'} to {'deck material': 'bamboo', 'length': '34 inch', 'design': 'graphic'}; Smartphone {'color': 'black', 'storage': '128GB', 'RAM': '8GB', 'screen size': '5.8-inch'} to {'RAM': '4GB', 'screen size': '6.5-inch'}; Bookshelf {'material': 'glass', 'color': 'white', 'height': '4 ft'} to {'color': 'black', 'height': '3 ft'}; via gift_card_7219486. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W8632528",
                    "item_ids": ["2185126308"],
                    "new_item_ids": ["8106223139"],
                    "payment_method_id": "credit_card_9789590",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W8073920",
                    "item_ids": ["8277474082", "9929635042", "5886093635"],
                    "new_item_ids": ["6159919747", "1507389580", "8573379326"],
                    "payment_method_id": "gift_card_7219486",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W6779827", "reason": "ordered by mistake"},
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6426438",
                    "item_ids": ["2177997696", "1507389580", "7373893106"],
                    "new_item_ids": ["3541421151", "5339029584", "1768466237"],
                    "payment_method_id": "gift_card_7219486",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mia_moore_8366",
        instruction="Your name is Mia Moore and your email is mia.moore8091@example.com. You are happy, rigid, pessimistic, confident. For #W5544629, exchange Electric Toothbrush {'color': 'blue', 'speed settings': 'low', 'battery type': 'AA batteries'} to {'color': 'white', 'battery type': 'rechargeable'}; via paypal_5181300. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W5544629",
                    "item_ids": ["1583904702"],
                    "new_item_ids": ["6164262152"],
                    "payment_method_id": "paypal_5181300",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mason_johansson_8128",
        instruction="Your name is Mason Johansson and your email is mason.johansson9549@example.com. You are shy, dependent. Return #W4352605 via gift_card_1401311: Laptop; Gaming Mouse; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W4352605",
                    "item_ids": ["2216662955", "8214883393"],
                    "payment_method_id": "gift_card_1401311",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lei_anderson_8271",
        instruction="Your name is Lei Anderson and your zip code is 76192. You are busy, impatient, pessimistic, rigid, cautious. Return #W4072946 via paypal_1808675: Action Camera; Hiking Boots; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W4072946",
                    "item_ids": ["5436236388", "8106223139"],
                    "payment_method_id": "paypal_1808675",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="fatima_wilson_7472",
        instruction="Your name is Fatima Wilson and your email is fatima.wilson5721@example.com. You are curious, happy, patient, flexible, confident. For #W5272531, exchange Espresso Machine {'pressure': '15 bar', 'capacity': '1.5L', 'type': 'capsule'} to {'pressure': '9 bar', 'capacity': '1L'}; via credit_card_6824399. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W5272531",
                    "item_ids": ["7441167885"],
                    "new_item_ids": ["7806008610"],
                    "payment_method_id": "credit_card_6824399",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="omar_santos_4830",
        instruction="Your name is Omar Santos and your zip code is 76180. You are creative, rigid, relaxing. Cancel order #W9121070 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W9121070", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="aarav_thomas_2711",
        instruction="Your name is Aarav Thomas and your zip code is 32175. You are logical, outgoing, independent. Cancel order #W5158064 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W5158064", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="juan_kim_6026",
        instruction="Your name is Juan Kim and your email is juan.kim2574@example.com. You are flexible, dependent. Return #W2002172 via paypal_5061070: Cycling Helmet; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W2002172",
                    "item_ids": ["9013366374"],
                    "payment_method_id": "paypal_5061070",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="daiki_johnson_9523",
        instruction="Your name is Daiki Johnson and your email is daiki.johnson2279@example.com. You are optimistic, direct, rigid, sad. Cancel order #W1436802 because no longer needed. For #W5282037, modify Garden Hose {'length': '25ft', 'material': 'latex', 'color': 'green'} to {'material': 'vinyl', 'color': 'blue'}; via paypal_2433177. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W1436802", "reason": "no longer needed"},
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W5282037",
                    "item_ids": ["3230708338"],
                    "new_item_ids": ["9829827210"],
                    "payment_method_id": "paypal_2433177",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_smith_9087",
        instruction="Your name is Ethan Smith and your email is ethan.smith2338@example.com. You are pessimistic, curious, direct, organized. Cancel order #W6711349 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W6711349", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_johnson_7053",
        instruction="Your name is Ethan Johnson and your zip code is 80298. You are sad, outgoing, flexible. Return #W5321777 via gift_card_6892585: Espresso Machine; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W5321777",
                    "item_ids": ["7441167885"],
                    "payment_method_id": "gift_card_6892585",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yara_moore_6466",
        instruction="Your name is Yara Moore and your zip code is 92162. You are shy, cautious, relaxing, independent. For #W1605168, exchange Tablet {'screen size': '7-inch', 'storage': '32GB', 'color': 'silver'} to {'screen size': '10-inch', 'storage': '128GB', 'color': 'gold'}; via credit_card_7161839. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W1605168",
                    "item_ids": ["4615543240"],
                    "new_item_ids": ["6948061616"],
                    "payment_method_id": "credit_card_7161839",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="fatima_anderson_2157",
        instruction="Your name is Fatima Anderson and your zip code is 32100. You are impatient, organized. For #W2974929, modify Skateboard {'deck material': 'plastic', 'length': '31 inch', 'design': 'plain'} to {'length': '34 inch', 'design': 'graphic'}; via paypal_7916550. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W2974929",
                    "item_ids": ["3877188862"],
                    "new_item_ids": ["5489028872"],
                    "payment_method_id": "paypal_7916550",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sophia_jackson_7119",
        instruction="Your name is Sophia Jackson and your email is sophia.jackson9875@example.com. You are outgoing, confident. Return #W3977493 via credit_card_6748580: Water Bottle {'capacity': '500ml', 'material': 'stainless steel', 'color': 'green'}; Electric Toothbrush; Laptop; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W3977493",
                    "item_ids": ["7533802601", "7144237253", "2216662955"],
                    "payment_method_id": "credit_card_6748580",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lei_anderson_8271",
        instruction="Your name is Lei Anderson and your zip code is 76192. You are shy, impatient, curious, insecure. Return #W7242815 via paypal_1808675: Tablet; For #W6002467, change address to {'order_id': '#W6002467', 'address1': '544 Sunset Drive', 'address2': 'Suite 337', 'city': 'Jacksonville', 'country': 'USA', 'state': 'FL', 'zip': '32205'} (same as #W1866533). For #W6002467, modify Dumbbell Set {'weight range': '55-75 lbs', 'material': 'rubber', 'set type': 'adjustable'} to {'weight range': '30-50 lbs', 'material': 'urethane', 'set type': 'fixed'}; via paypal_1808675. ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W7242815",
                    "item_ids": ["6948061616"],
                    "payment_method_id": "paypal_1808675",
                },
            ),
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W6002467",
                    "address1": "544 Sunset Drive",
                    "address2": "Suite 337",
                    "city": "Jacksonville",
                    "country": "USA",
                    "state": "FL",
                    "zip": "32205",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6002467",
                    "item_ids": ["8140269513"],
                    "new_item_ids": ["7159180318"],
                    "payment_method_id": "paypal_1808675",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sofia_thomas_1518",
        instruction="Your name is Sofia Thomas and your zip code is 75307. You are creative, independent, cautious, rigid, organized. For #W2297866, modify Vacuum Cleaner {'type': 'upright', 'bagged/bagless': 'bagless', 'features': 'HEPA filter'} to {'type': 'robotic', 'bagged/bagless': 'bagged', 'features': 'cordless'}; via paypal_5334408. Cancel order #W7619352 because ordered by mistake. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W2297866",
                    "item_ids": ["7407609582"],
                    "new_item_ids": ["4602305039"],
                    "payment_method_id": "paypal_5334408",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W7619352", "reason": "ordered by mistake"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="harper_brown_7363",
        instruction="Your name is Harper Brown and your zip code is 76112. You are organized, patient, sad, dependent, cautious. For #W2273069, change payment to paypal_2306935. For #W2273069, modify Smart Watch {'color': 'gold', 'band material': 'silicone', 'display': 'AMOLED'} to {'band material': 'leather', 'display': 'LCD'}; Electric Toothbrush {'color': 'black', 'speed settings': 'high', 'battery type': 'rechargeable'} to {}; Hiking Boots {'size': '10', 'material': 'leather', 'waterproof': 'no'} to {'size': '11', 'waterproof': 'yes'}; via paypal_2306935. For #W2693718, exchange Digital Camera {'resolution': '30MP', 'zoom': '3x', 'storage': 'CF card'} to {'resolution': '24MP', 'storage': 'SD card'}; via credit_card_3240550. ",
        actions=[
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W2273069",
                    "payment_method_id": "paypal_2306935",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W2273069",
                    "item_ids": ["2681513500", "8098621301", "2185126308"],
                    "new_item_ids": ["9408160950", "8098621301", "6159919747"],
                    "payment_method_id": "paypal_2306935",
                },
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W2693718",
                    "item_ids": ["7255224608"],
                    "new_item_ids": ["5996159312"],
                    "payment_method_id": "credit_card_3240550",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="daiki_patel_5953",
        instruction="Your name is Daiki Patel and your zip code is 94111. You are organized, flexible, optimistic, happy. For #W8969494, exchange Mechanical Keyboard {'switch type': 'clicky', 'backlight': 'RGB', 'size': '60%'} to {'switch type': 'linear', 'size': '80%'}; via paypal_1009053. For #W8068454, exchange Bookshelf {'material': 'wood', 'color': 'brown', 'height': '6 ft'} to {'color': 'white', 'height': '5 ft'}; Cycling Helmet {'size': 'S', 'color': 'black', 'ventilation': 'medium'} to {'size': 'M', 'color': 'blue', 'ventilation': 'high'}; Air Purifier {'room size': 'medium', 'filter type': 'HEPA', 'features': 'night mode'} to {'room size': 'large'}; Bluetooth Speaker {'color': 'green', 'battery life': '10 hours', 'water resistance': 'no'} to {'color': 'red', 'water resistance': 'yes'}; via paypal_1009053. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W8969494",
                    "item_ids": ["9690244451"],
                    "new_item_ids": ["8484921793"],
                    "payment_method_id": "paypal_1009053",
                },
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W8068454",
                    "item_ids": [
                        "7154215719",
                        "5537798301",
                        "1327854740",
                        "9179378709",
                    ],
                    "new_item_ids": [
                        "8479046075",
                        "9013366374",
                        "8302289002",
                        "7751905257",
                    ],
                    "payment_method_id": "paypal_1009053",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mia_garcia_4516",
        instruction="Your name is Mia Garcia and your zip code is 46229. You are independent, direct, flexible. Return #W5490111 via credit_card_3124723: Action Camera; Backpack; Water Bottle; Mechanical Keyboard; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W5490111",
                    "item_ids": [
                        "6117189161",
                        "4947717507",
                        "4579334072",
                        "1421289881",
                    ],
                    "payment_method_id": "credit_card_3124723",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mia_smith_1623",
        instruction="Your name is Mia Smith and your zip code is 80246. You are logical, independent, direct, impatient, sad. Return #W2922379 via paypal_3839332: Water Bottle; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W2922379",
                    "item_ids": ["7661609223"],
                    "payment_method_id": "paypal_3839332",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_davis_3316",
        instruction="Your name is Olivia Davis and your zip code is 77244. You are flexible, polite. For #W7623533, exchange Jigsaw Puzzle {'pieces': '1000', 'theme': 'animals', 'difficulty level': 'beginner'} to {'pieces': '1500', 'theme': 'art', 'difficulty level': 'intermediate'}; via paypal_8673863. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W7623533",
                    "item_ids": ["4772738468"],
                    "new_item_ids": ["5546244844"],
                    "payment_method_id": "paypal_8673863",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="fatima_muller_6713",
        instruction="Your name is Fatima Muller and your zip code is 60644. You are confident, optimistic, polite, messy, independent. For #W6851636, modify Running Shoes {'size': '8', 'color': 'red', 'material': 'leather', 'sole': 'EVA'} to {'size': '10', 'color': 'white'}; via paypal_5541158. Return #W2435638 via paypal_5541158: Bookshelf; Digital Camera; Gaming Mouse; Garden Hose; Espresso Machine; For #W2040365, change address to {'order_id': '#W2040365', 'address1': '377 River Road', 'address2': 'Suite 307', 'city': 'Chicago', 'country': 'USA', 'state': 'IL', 'zip': '60644'} (same as #W9962383). For #W2040365, modify Espresso Machine {'pressure': '9 bar', 'capacity': '2L', 'type': 'automatic'} to {'pressure': '15 bar', 'capacity': '1L', 'type': 'manual'}; via paypal_5541158. Cancel order #W9962383 because ordered by mistake. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6851636",
                    "item_ids": ["4153505238"],
                    "new_item_ids": ["1775591963"],
                    "payment_method_id": "paypal_5541158",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W2435638",
                    "item_ids": [
                        "8895454203",
                        "7583936705",
                        "8896479688",
                        "1518544029",
                        "7441167885",
                    ],
                    "payment_method_id": "paypal_5541158",
                },
            ),
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W2040365",
                    "address1": "377 River Road",
                    "address2": "Suite 307",
                    "city": "Chicago",
                    "country": "USA",
                    "state": "IL",
                    "zip": "60644",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W2040365",
                    "item_ids": ["3709608322"],
                    "new_item_ids": ["3714494375"],
                    "payment_method_id": "paypal_5541158",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W9962383", "reason": "ordered by mistake"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="daiki_muller_8062",
        instruction="Your name is Daiki Muller and your zip code is 94157. You are patient, sad. For #W6790887, modify Dumbbell Set {'weight range': '5-25 lbs', 'material': 'urethane', 'set type': 'fixed'} to {'weight range': '30-50 lbs', 'set type': 'adjustable'}; via gift_card_8385925. For #W7822344, modify Electric Kettle {'capacity': '1L', 'material': 'stainless steel', 'color': 'silver'} to {'color': 'black'}; via gift_card_8385925. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6790887",
                    "item_ids": ["6585768447"],
                    "new_item_ids": ["4422467033"],
                    "payment_method_id": "gift_card_8385925",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W7822344",
                    "item_ids": ["8142779083"],
                    "new_item_ids": ["7602931732"],
                    "payment_method_id": "gift_card_8385925",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="daiki_davis_5031",
        instruction="Your name is Daiki Davis and your zip code is 94102. You are curious, pessimistic, flexible, relaxing, independent. For #W5457973, exchange Indoor Security Camera {'resolution': '1080p', 'field of view': '160 degrees', 'connectivity': 'Ethernet'} to {'resolution': '2K', 'field of view': '130 degrees'}; via gift_card_1679693. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W5457973",
                    "item_ids": ["1569829406"],
                    "new_item_ids": ["8470360507"],
                    "payment_method_id": "gift_card_1679693",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="emma_santos_9753",
        instruction="Your name is Emma Santos and your zip code is 78228. You are dependent, impatient, relaxing. Cancel order #W1620235 because no longer needed. Cancel order #W2918688 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W1620235", "reason": "no longer needed"},
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W2918688", "reason": "no longer needed"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="noah_sanchez_2690",
        instruction="Your name is Noah Sanchez and your email is noah.sanchez7461@example.com. You are flexible, busy. Cancel order #W8645374 because ordered by mistake. For #W7293142, exchange Hiking Boots {'size': '10', 'material': 'leather', 'waterproof': 'no'} to {'size': '11'}; Mechanical Keyboard {'switch type': 'clicky', 'backlight': 'RGB', 'size': 'full size'} to {'switch type': 'linear', 'backlight': 'none'}; via gift_card_9909795. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W8645374", "reason": "ordered by mistake"},
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W7293142",
                    "item_ids": ["2185126308", "9025753381"],
                    "new_item_ids": ["5676696062", "9570044148"],
                    "payment_method_id": "gift_card_9909795",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sophia_garcia_5795",
        instruction="Your name is Sophia Garcia and your zip code is 28212. You are organized, curious, impatient. For #W4958652, change address to {'order_id': '#W4958652', 'address1': '536 Cedar Street', 'address2': 'Suite 916', 'city': 'Charlotte', 'country': 'USA', 'state': 'NC', 'zip': '28212'} (same as #W6447372). For #W4958652, modify Cycling Helmet {'size': 'L', 'color': 'black', 'ventilation': 'high'} to {'size': 'S', 'color': 'blue', 'ventilation': 'low'}; Tea Kettle {'material': 'stainless steel', 'capacity': '2 liters', 'stovetop compatibility': 'induction'} to {'material': 'glass'}; Office Chair {'material': 'fabric', 'color': 'blue', 'armrest': 'adjustable', 'backrest height': 'standard'} to {'material': 'mesh', 'color': 'red', 'armrest': 'none'}; Smart Thermostat {'compatibility': 'Google Assistant', 'color': 'stainless steel'} to {'compatibility': 'Apple HomeKit', 'color': 'black'}; via credit_card_9467292. ",
        actions=[
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W4958652",
                    "address1": "536 Cedar Street",
                    "address2": "Suite 916",
                    "city": "Charlotte",
                    "country": "USA",
                    "state": "NC",
                    "zip": "28212",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W4958652",
                    "item_ids": [
                        "1665571435",
                        "1906487464",
                        "8323284863",
                        "2791467853",
                    ],
                    "new_item_ids": [
                        "5886093635",
                        "7292993796",
                        "4274709903",
                        "4983901480",
                    ],
                    "payment_method_id": "credit_card_9467292",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lucas_brown_6720",
        instruction="Your name is Lucas Brown and your zip code is 60612. You are rigid, polite, cautious, confident. Return #W8660475 via credit_card_2112420: Office Chair; Return #W6239298 via credit_card_2112420: Water Bottle; Bookshelf; Jigsaw Puzzle; For #W4860251, change address to {'order_id': '#W4860251', 'address1': '921 Park Avenue', 'address2': 'Suite 892', 'city': 'Chicago', 'country': 'USA', 'state': 'IL', 'zip': '60612'} (same as #W6239298). For #W4860251, modify Luggage Set {'piece count': '2-piece', 'color': 'silver', 'material': 'hardshell'} to {'piece count': '4-piece', 'color': 'blue', 'material': 'softshell'}; via credit_card_2112420. ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W8660475",
                    "item_ids": ["8323284863"],
                    "payment_method_id": "credit_card_2112420",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W6239298",
                    "item_ids": ["2366567022", "4900661478", "3614853563"],
                    "payment_method_id": "credit_card_2112420",
                },
            ),
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W4860251",
                    "address1": "921 Park Avenue",
                    "address2": "Suite 892",
                    "city": "Chicago",
                    "country": "USA",
                    "state": "IL",
                    "zip": "60612",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W4860251",
                    "item_ids": ["5209958006"],
                    "new_item_ids": ["8759627937"],
                    "payment_method_id": "credit_card_2112420",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="liam_nguyen_9081",
        instruction="Your name is Liam Nguyen and your zip code is 95184. You are organized, independent, creative. For #W3919881, exchange Espresso Machine {'pressure': '19 bar', 'capacity': '1L', 'type': 'capsule'} to {'pressure': '15 bar', 'type': 'manual'}; via paypal_3226997. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W3919881",
                    "item_ids": ["6200867091"],
                    "new_item_ids": ["3714494375"],
                    "payment_method_id": "paypal_3226997",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_muller_6097",
        instruction="Your name is Ethan Muller and your email is ethan.muller6617@example.com. You are relaxing, sad. Cancel order #W4683557 because ordered by mistake. Return #W4398027 via credit_card_5721095: Perfume; ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W4683557", "reason": "ordered by mistake"},
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W4398027",
                    "item_ids": ["1725100896"],
                    "payment_method_id": "credit_card_5721095",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mei_kovacs_8020",
        instruction="Your name is Mei Kovacs and your email is mei.kovacs8232@example.com. You are rigid, curious, insecure, relaxing, independent. For #W8065207, exchange Garden Hose {'length': '50ft', 'material': 'latex', 'color': 'black'} to {}; Smart Watch {'color': 'gold', 'band material': 'leather', 'display': 'AMOLED'} to {'color': 'black', 'band material': 'silicone', 'display': 'LCD'}; via paypal_7644869. Return #W6390527 via paypal_7644869: Hiking Boots; Water Bottle; ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W8065207",
                    "item_ids": ["4024196380", "5694328282"],
                    "new_item_ids": ["4024196380", "2860956907"],
                    "payment_method_id": "paypal_7644869",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W6390527",
                    "item_ids": ["1615379700", "8538875209"],
                    "payment_method_id": "paypal_7644869",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="amelia_wilson_4614",
        instruction="Your name is Amelia Wilson and your email is amelia.wilson1598@example.com. You are confident, cautious, dependent, shy, pessimistic. Cancel order #W3062096 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W3062096", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ava_lopez_2676",
        instruction="Your name is Ava Lopez and your zip code is 92168. You are polite, messy, busy, patient, flexible. For #W5911003, modify Office Chair {'material': 'mesh', 'color': 'red', 'armrest': 'none', 'backrest height': 'standard'} to {'material': 'fabric', 'color': 'black', 'armrest': 'fixed'}; via gift_card_4855547. For #W2941275, exchange Digital Camera {'resolution': '30MP', 'zoom': '3x', 'storage': 'SD card'} to {'storage': 'CF card'}; Water Bottle {'capacity': '750ml', 'material': 'stainless steel', 'color': 'blue'} to {'capacity': '500ml', 'material': 'glass', 'color': 'green'}; via credit_card_7772870. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W5911003",
                    "item_ids": ["4274709903"],
                    "new_item_ids": ["8426249116"],
                    "payment_method_id": "gift_card_4855547",
                },
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W2941275",
                    "item_ids": ["1804581713", "7843064651"],
                    "new_item_ids": ["7255224608", "5758737025"],
                    "payment_method_id": "credit_card_7772870",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="noah_khan_5763",
        instruction="Your name is Noah Khan and your email is noah.khan7453@example.com. You are pessimistic, creative, insecure, messy. For #W1483350, exchange Cycling Helmet {'size': 'L', 'color': 'white', 'ventilation': 'medium'} to {'size': 'M', 'color': 'blue', 'ventilation': 'high'}; Mechanical Keyboard {'switch type': 'linear', 'backlight': 'none', 'size': 'full size'} to {'switch type': 'clicky', 'backlight': 'white'}; via paypal_2319812. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W1483350",
                    "item_ids": ["6697922351", "9570044148"],
                    "new_item_ids": ["9013366374", "6342039236"],
                    "payment_method_id": "paypal_2319812",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="evelyn_lopez_5487",
        instruction="Your name is Evelyn Lopez and your zip code is 92195. You are impatient, busy. Cancel order #W3007862 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W3007862", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ava_nguyen_4072",
        instruction="Your name is Ava Nguyen and your email is ava.nguyen1851@example.com. You are relaxing, curious. For #W2601346, modify Makeup Kit {'skin tone': 'medium', 'kit size': 'professional', 'brand': 'Brand C'} to {'skin tone': 'dark', 'brand': 'Brand A'}; via paypal_3180577. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W2601346",
                    "item_ids": ["7736359414"],
                    "new_item_ids": ["1573035764"],
                    "payment_method_id": "paypal_3180577",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lucas_muller_4380",
        instruction="Your name is Lucas Muller and your zip code is 78763. You are shy, messy, patient. Return #W1523776 via gift_card_2748512: Smart Thermostat; Makeup Kit; Cancel order #W3206099 because ordered by mistake. ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W1523776",
                    "item_ids": ["8593894906", "3913310464"],
                    "payment_method_id": "gift_card_2748512",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W3206099", "reason": "ordered by mistake"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="harper_thomas_9402",
        instruction="Your name is Harper Thomas and your email is harper.thomas1454@example.com. You are messy, happy, cautious. Cancel order #W7425646 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W7425646", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mason_johansson_8128",
        instruction="Your name is Mason Johansson and your zip code is 98103. You are outgoing, busy. For #W4352605, exchange Laptop {'screen size': '15-inch', 'processor': 'i5', 'ram': '32GB', 'storage': '256GB SSD', 'color': 'space grey'} to {'screen size': '13-inch', 'ram': '16GB', 'storage': '512GB SSD'}; via gift_card_1401311. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W4352605",
                    "item_ids": ["2216662955"],
                    "new_item_ids": ["6056040996"],
                    "payment_method_id": "gift_card_1401311",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_rossi_9620",
        instruction="Your name is Yusuf Rossi and your zip code is 19122. You are sad, logical, polite, independent. Return #W2378156 via credit_card_9513926: Smart Thermostat; Smart Watch; Vacuum Cleaner; Mechanical Keyboard; For #W4776164, modify Espresso Machine {'pressure': '9 bar', 'capacity': '1L', 'type': 'automatic'} to {'capacity': '1.5L', 'type': 'capsule'}; via credit_card_9513926. ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W2378156",
                    "item_ids": [
                        "4983901480",
                        "9408160950",
                        "4602305039",
                        "1151293680",
                    ],
                    "payment_method_id": "credit_card_9513926",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W4776164",
                    "item_ids": ["6324294385"],
                    "new_item_ids": ["3815173328"],
                    "payment_method_id": "credit_card_9513926",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="fatima_anderson_2157",
        instruction="Your name is Fatima Anderson and your email is fatima.anderson1447@example.com. You are busy, curious, insecure, dependent. Cancel order #W4514908 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W4514908", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="aarav_gonzalez_5113",
        instruction="Your name is Aarav Gonzalez and your email is aarav.gonzalez9269@example.com. You are relaxing, creative, happy, pessimistic. Cancel order #W6979932 because ordered by mistake. Cancel order #W9160732 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W6979932", "reason": "ordered by mistake"},
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W9160732", "reason": "ordered by mistake"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mohamed_smith_9224",
        instruction="Your name is Mohamed Smith and your email is mohamed.smith3152@example.com. You are curious, busy. For #W7808613, exchange Smart Watch {'color': 'silver', 'band material': 'leather', 'display': 'LCD'} to {'color': 'gold', 'display': 'AMOLED'}; via credit_card_7801956. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W7808613",
                    "item_ids": ["9811090008"],
                    "new_item_ids": ["5694328282"],
                    "payment_method_id": "credit_card_7801956",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_lopez_3865",
        instruction="Your name is Olivia Lopez and your zip code is 76171. You are outgoing, messy. For #W7449508, exchange Sneakers {'size': '6', 'color': 'black', 'material': 'synthetic'} to {'size': '10', 'color': 'gray', 'material': 'leather'}; via gift_card_7711863. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W7449508",
                    "item_ids": ["6477915553"],
                    "new_item_ids": ["2509076505"],
                    "payment_method_id": "gift_card_7711863",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="harper_ahmed_4844",
        instruction="Your name is Harper Ahmed and your email is harper.ahmed7911@example.com. You are organized, dependent, happy, insecure, impatient. For #W5911118, exchange Skateboard {'deck material': 'maple', 'length': '31 inch', 'design': 'graphic'} to {'deck material': 'bamboo', 'length': '34 inch'}; via gift_card_4529075. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W5911118",
                    "item_ids": ["5120532699"],
                    "new_item_ids": ["3541421151"],
                    "payment_method_id": "gift_card_4529075",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_ito_3591",
        instruction="Your name is Olivia Ito and your zip code is 80218. You are logical, curious. For #W7941031, change payment to paypal_8049766. For #W7941031, modify Backpack {'color': 'grey', 'size': 'medium', 'material': 'polyester', 'compartment': 'laptop'} to {'size': 'small', 'material': 'nylon'}; via gift_card_7794233. ",
        actions=[
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W7941031",
                    "payment_method_id": "paypal_8049766",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W7941031",
                    "item_ids": ["5917587651"],
                    "new_item_ids": ["8054888773"],
                    "payment_method_id": "gift_card_7794233",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="anya_brown_2024",
        instruction="Your name is Anya Brown and your zip code is 10121. You are insecure, logical, sad, messy. For #W1430028, modify Running Shoes {'size': '9', 'color': 'black', 'material': 'synthetic', 'sole': 'rubber'} to {'color': 'yellow'}; Vacuum Cleaner {'type': 'robotic', 'bagged/bagless': 'bagless', 'features': 'pet hair removal'} to {'features': 'cordless'}; via paypal_5206520. Return #W2922433 via credit_card_3414703: Tablet; Grill; Makeup Kit; Cancel order #W8883368 because ordered by mistake. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W1430028",
                    "item_ids": ["4107812777", "4965355367"],
                    "new_item_ids": ["9791469541", "4806644905"],
                    "payment_method_id": "paypal_5206520",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W2922433",
                    "item_ids": ["4913411651", "5745575001", "1709726483"],
                    "payment_method_id": "credit_card_3414703",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W8883368", "reason": "ordered by mistake"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="chen_johnson_4204",
        instruction="Your name is Chen Johnson and your email is chen.johnson3889@example.com. You are happy, flexible, impatient, shy, messy. Return #W5797164 via gift_card_3406421: Jigsaw Puzzle; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W5797164",
                    "item_ids": ["9237024510"],
                    "payment_method_id": "gift_card_3406421",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="anya_thomas_1213",
        instruction="Your name is Anya Thomas and your email is anya.thomas9688@example.com. You are organized, relaxing. For #W7909132, exchange Bicycle {'frame size': 'medium', 'color': 'green', 'type': 'road'} to {'color': 'black', 'type': 'mountain'}; via paypal_2557789. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W7909132",
                    "item_ids": ["7758198585"],
                    "new_item_ids": ["2143041831"],
                    "payment_method_id": "paypal_2557789",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_sanchez_7289",
        instruction="Your name is Ethan Sanchez and your email is ethan.sanchez3299@example.com. You are flexible, dependent, happy, cautious, polite. For #W5560533, exchange Smart Watch {'color': 'gold', 'band material': 'metal', 'display': 'AMOLED'} to {'band material': 'silicone'}; via gift_card_5917510. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W5560533",
                    "item_ids": ["2554056026"],
                    "new_item_ids": ["2681513500"],
                    "payment_method_id": "gift_card_5917510",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="fatima_brown_5229",
        instruction="Your name is Fatima Brown and your email is fatima.brown7817@example.com. You are pessimistic, rigid. Return #W9045919 via gift_card_8633125: Smart Thermostat; Digital Camera; Cycling Helmet; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W9045919",
                    "item_ids": ["4953074738", "1804581713", "1719127154"],
                    "payment_method_id": "gift_card_8633125",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sofia_ahmed_9514",
        instruction="Your name is Sofia Ahmed and your email is sofia.ahmed2872@example.com. You are rigid, messy, creative. Cancel order #W4806309 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W4806309", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="liam_ahmed_6523",
        instruction="Your name is Liam Ahmed and your email is liam.ahmed8540@example.com. You are independent, polite, insecure. Cancel order #W1558044 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W1558044", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sofia_davis_2103",
        instruction="Your name is Sofia Davis and your zip code is 98151. You are pessimistic, insecure, messy, direct, curious. For #W2541482, modify Espresso Machine {'pressure': '15 bar', 'capacity': '1L', 'type': 'manual'} to {'pressure': '9 bar', 'capacity': '1.5L', 'type': 'capsule'}; Tea Kettle {'material': 'ceramic', 'capacity': '1.5 liters', 'stovetop compatibility': 'gas'} to {'material': 'glass', 'capacity': '2 liters', 'stovetop compatibility': 'electric'}; via gift_card_3377580. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W2541482",
                    "item_ids": ["3714494375", "7497340597"],
                    "new_item_ids": ["3815173328", "2820119811"],
                    "payment_method_id": "gift_card_3377580",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_moore_3587",
        instruction="Your name is Ethan Moore and your email is ethan.moore4935@example.com. You are happy, insecure. For #W7584328, modify Backpack {'color': 'navy', 'size': 'small', 'material': 'nylon', 'compartment': 'laptop'} to {'color': 'black', 'size': 'large', 'material': 'polyester'}; via credit_card_6173085. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W7584328",
                    "item_ids": ["2492465580"],
                    "new_item_ids": ["6906307980"],
                    "payment_method_id": "credit_card_6173085",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="aarav_davis_4756",
        instruction="Your name is Aarav Davis and your zip code is 76150. You are busy, happy, direct, impatient, dependent. For #W7430166, change address to {'order_id': '#W7430166', 'address1': '808 Chestnut Street', 'address2': 'Suite 832', 'city': 'Phoenix', 'country': 'USA', 'state': 'AZ', 'zip': '85072'} (same as #W2403075). For #W7430166, modify Headphones {'type': 'in-ear', 'connectivity': 'wired', 'color': 'red'} to {'type': 'on-ear', 'connectivity': 'wireless'}; via gift_card_9708163. For #W3223435, exchange Garden Hose {'length': '25ft', 'material': 'latex', 'color': 'green'} to {'material': 'vinyl'}; via gift_card_9708163. ",
        actions=[
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W7430166",
                    "address1": "808 Chestnut Street",
                    "address2": "Suite 832",
                    "city": "Phoenix",
                    "country": "USA",
                    "state": "AZ",
                    "zip": "85072",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W7430166",
                    "item_ids": ["1133777903"],
                    "new_item_ids": ["3104857380"],
                    "payment_method_id": "gift_card_9708163",
                },
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W3223435",
                    "item_ids": ["3230708338"],
                    "new_item_ids": ["3369928769"],
                    "payment_method_id": "gift_card_9708163",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mason_wilson_4597",
        instruction="Your name is Mason Wilson and your email is mason.wilson6954@example.com. You are dependent, cautious, shy. Return #W8161562 via gift_card_6767859: Digital Camera; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W8161562",
                    "item_ids": ["7195021808"],
                    "payment_method_id": "gift_card_6767859",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_hernandez_6785",
        instruction="Your name is Yusuf Hernandez and your zip code is 80265. You are confident, flexible. For #W6832752, change address to {'order_id': '#W6832752', 'address1': '580 Broadway', 'address2': 'Suite 162', 'city': 'Denver', 'country': 'USA', 'state': 'CO', 'zip': '80265'} (same as #W2166301). For #W6832752, modify Hiking Boots {'size': '7', 'material': 'leather', 'waterproof': 'yes'} to {'material': 'synthetic', 'waterproof': 'no'}; via paypal_7529813. For #W2166301, modify Running Shoes {'size': '10', 'color': 'white', 'material': 'leather', 'sole': 'EVA'} to {'size': '8', 'color': 'red'}; via paypal_7529813. ",
        actions=[
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W6832752",
                    "address1": "580 Broadway",
                    "address2": "Suite 162",
                    "city": "Denver",
                    "country": "USA",
                    "state": "CO",
                    "zip": "80265",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6832752",
                    "item_ids": ["3812493782"],
                    "new_item_ids": ["1437889264"],
                    "payment_method_id": "paypal_7529813",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W2166301",
                    "item_ids": ["1775591963"],
                    "new_item_ids": ["4153505238"],
                    "payment_method_id": "paypal_7529813",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="evelyn_hernandez_1701",
        instruction="Your name is Evelyn Hernandez and your zip code is 92139. You are logical, cautious, confident. For #W9628587, exchange Bookshelf {'material': 'glass', 'color': 'black', 'height': '5 ft'} to {'material': 'wood', 'height': '4 ft'}; via credit_card_3631888. Cancel order #W3482034 because no longer needed. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W9628587",
                    "item_ids": ["4900661478"],
                    "new_item_ids": ["1673859111"],
                    "payment_method_id": "credit_card_3631888",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W3482034", "reason": "no longer needed"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="noah_sanchez_2690",
        instruction="Your name is Noah Sanchez and your zip code is 20056. You are patient, flexible, outgoing, pessimistic, dependent. For #W4864669, exchange Digital Camera {'resolution': '30MP', 'zoom': '10x', 'storage': 'SD card'} to {'resolution': '24MP', 'zoom': '3x'}; Wireless Earbuds {'color': 'black', 'battery life': '4 hours', 'water resistance': 'IPX7'} to {'color': 'blue', 'battery life': '8 hours', 'water resistance': 'IPX4'}; via gift_card_9909795. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W4864669",
                    "item_ids": ["9228757377", "9580569596"],
                    "new_item_ids": ["5996159312", "8555936349"],
                    "payment_method_id": "gift_card_9909795",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lei_hernandez_8500",
        instruction="Your name is Lei Hernandez and your zip code is 43222. You are shy, curious, polite, dependent. Return #W6146740 via gift_card_5245016: Hiking Boots; Laptop; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W6146740",
                    "item_ids": ["8118291112", "6056040996"],
                    "payment_method_id": "gift_card_5245016",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="fatima_johnson_7581",
        instruction="Your name is Fatima Johnson and your email is fatima.johnson2300@example.com. You are busy, sad. For #W9389413, exchange T-Shirt {'color': 'blue', 'size': 'S', 'material': 'polyester', 'style': 'v-neck'} to {'color': 'purple'}; via gift_card_1675628. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W9389413",
                    "item_ids": ["5047954489"],
                    "new_item_ids": ["9647292434"],
                    "payment_method_id": "gift_card_1675628",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yara_muller_8652",
        instruction="Your name is Yara Muller and your email is yara.muller9246@example.com. You are rigid, shy, confident. Cancel order #W5056519 because no longer needed. For #W5995614, modify Dumbbell Set {'weight range': '5-25 lbs', 'material': 'iron', 'set type': 'adjustable'} to {'weight range': '30-50 lbs', 'material': 'rubber'}; Luggage Set {'piece count': '3-piece', 'color': 'black', 'material': 'softshell'} to {'piece count': '2-piece'}; via credit_card_3095586. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W5056519", "reason": "no longer needed"},
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W5995614",
                    "item_ids": ["3877338112", "9692325258"],
                    "new_item_ids": ["3735133539", "8926329222"],
                    "payment_method_id": "credit_card_3095586",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="raj_davis_2615",
        instruction="Your name is Raj Davis and your zip code is 85050. You are optimistic, flexible, creative, happy, impatient. For #W9894882, exchange Bicycle {'frame size': 'medium', 'color': 'blue', 'type': 'road'} to {'frame size': 'large', 'color': 'red', 'type': 'mountain'}; via gift_card_8006222. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W9894882",
                    "item_ids": ["3624655057"],
                    "new_item_ids": ["5606522780"],
                    "payment_method_id": "gift_card_8006222",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="raj_ito_1740",
        instruction="Your name is Raj Ito and your zip code is 60641. You are rigid, relaxing, creative, shy. For #W8448267, exchange Perfume {'scent family': 'oriental', 'size': '30ml', 'gender': 'unisex'} to {'scent family': 'woody', 'gender': 'men'}; via credit_card_6480285. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W8448267",
                    "item_ids": ["1725100896"],
                    "new_item_ids": ["5081446110"],
                    "payment_method_id": "credit_card_6480285",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="anya_lee_8315",
        instruction="Your name is Anya Lee and your zip code is 78227. You are outgoing, polite, patient, logical, independent. Return #W1335809 via paypal_3728317: Hiking Boots; Espresso Machine; Cancel order #W2989580 because ordered by mistake. ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W1335809",
                    "item_ids": ["2185126308", "4875647558"],
                    "payment_method_id": "paypal_3728317",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W2989580", "reason": "ordered by mistake"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="harper_li_7655",
        instruction="Your name is Harper Li and your zip code is 32253. You are happy, pessimistic. Return #W9495141 via gift_card_8862145: Tablet; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W9495141",
                    "item_ids": ["6501071631"],
                    "payment_method_id": "gift_card_8862145",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mia_jackson_2250",
        instruction="Your name is Mia Jackson and your email is mia.jackson5798@example.com. You are busy, polite, independent, insecure, shy. Cancel order #W7807323 because ordered by mistake. For #W2618034, change address to {'order_id': '#W2618034', 'address1': '816 Spruce Street', 'address2': 'Suite 114', 'city': 'Indianapolis', 'country': 'USA', 'state': 'IN', 'zip': '46227'} (same as #W7807323). For #W2618034, modify Grill {'type': 'electric', 'size': 'portable', 'features': 'rotisserie'} to {'type': 'charcoal', 'size': 'medium', 'features': 'side burner'}; via gift_card_5715854. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W7807323", "reason": "ordered by mistake"},
            ),
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W2618034",
                    "address1": "816 Spruce Street",
                    "address2": "Suite 114",
                    "city": "Indianapolis",
                    "country": "USA",
                    "state": "IN",
                    "zip": "46227",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W2618034",
                    "item_ids": ["5745575001"],
                    "new_item_ids": ["7848293342"],
                    "payment_method_id": "gift_card_5715854",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sofia_ito_7804",
        instruction="Your name is Sofia Ito and your email is sofia.ito7258@example.com. You are busy, independent, flexible. For #W6075915, exchange Fleece Jacket {'size': 'M', 'color': 'black', 'zipper': 'full'} to {'size': 'S', 'color': 'red', 'zipper': 'half'}; Yoga Mat {'thickness': '6mm', 'material': 'PVC', 'color': 'green'} to {}; via credit_card_7039111. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W6075915",
                    "item_ids": ["4728397765", "7510236436"],
                    "new_item_ids": ["5992316252", "7510236436"],
                    "payment_method_id": "credit_card_7039111",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ava_nguyen_6646",
        instruction="Your name is Ava Nguyen and your zip code is 94128. You are relaxing, cautious, organized, logical. For #W6272294, change payment to credit_card_5683823. For #W6272294, modify Jigsaw Puzzle {'pieces': '1000', 'theme': 'animals', 'difficulty level': 'expert'} to {'pieces': '1500', 'difficulty level': 'intermediate'}; via gift_card_1994993. Return #W8668939 via credit_card_5683823: Water Bottle; For #W1242543, modify Skateboard {'deck material': 'plastic', 'length': '34 inch', 'design': 'custom'} to {'deck material': 'bamboo', 'length': '28 inch', 'design': 'plain'}; via credit_card_5683823. Cancel order #W8367380 because no longer needed. ",
        actions=[
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W6272294",
                    "payment_method_id": "credit_card_5683823",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6272294",
                    "item_ids": ["4572024853"],
                    "new_item_ids": ["6245746168"],
                    "payment_method_id": "gift_card_1994993",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W8668939",
                    "item_ids": ["7199146548"],
                    "payment_method_id": "credit_card_5683823",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W1242543",
                    "item_ids": ["9594745976"],
                    "new_item_ids": ["8176740019"],
                    "payment_method_id": "credit_card_5683823",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W8367380", "reason": "no longer needed"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="fatima_wilson_7472",
        instruction="Your name is Fatima Wilson and your zip code is 92183. You are patient, dependent, flexible, creative, optimistic. For #W5272531, exchange Electric Kettle {'capacity': '1.5L', 'material': 'plastic', 'color': 'white'} to {'capacity': '1L'}; Electric Toothbrush {'color': 'black', 'speed settings': 'high', 'battery type': 'rechargeable'} to {'color': 'white', 'battery type': 'AA batteries'}; Espresso Machine {'pressure': '15 bar', 'capacity': '1.5L', 'type': 'capsule'} to {'pressure': '19 bar', 'capacity': '2L', 'type': 'manual'}; via credit_card_6824399. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W5272531",
                    "item_ids": ["2698416822", "8098621301", "7441167885"],
                    "new_item_ids": ["2243454707", "2645006275", "3379843752"],
                    "payment_method_id": "credit_card_6824399",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="isabella_johansson_7408",
        instruction="Your name is Isabella Johansson and your email is isabella.johansson1233@example.com. You are organized, shy. Cancel order #W8882972 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W8882972", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="harper_johansson_2663",
        instruction="Your name is Harper Johansson and your zip code is 80281. You are sad, pessimistic, busy, creative, curious. Cancel order #W3525030 because no longer needed. For #W4866703, change address to {'order_id': '#W4866703', 'address1': '953 Park Avenue', 'address2': 'Suite 613', 'city': 'New York', 'country': 'USA', 'state': 'NY', 'zip': '10064'} (same as #W1780552). For #W4866703, modify Electric Kettle {'capacity': '1L', 'material': 'stainless steel', 'color': 'silver'} to {'material': 'glass', 'color': 'white'}; Office Chair {'material': 'fabric', 'color': 'black', 'armrest': 'fixed', 'backrest height': 'standard'} to {'material': 'leather', 'armrest': 'adjustable', 'backrest height': 'high-back'}; Office Chair {'material': 'fabric', 'color': 'black', 'armrest': 'none', 'backrest height': 'high-back'} to {'material': 'leather', 'color': 'gray', 'armrest': 'fixed'}; via paypal_4820484. Cancel order #W9677982 because no longer needed. For #W2912646, modify Jigsaw Puzzle {'pieces': '500', 'theme': 'art', 'difficulty level': 'beginner'} to {'theme': 'animals', 'difficulty level': 'expert'}; Luggage Set {'piece count': '3-piece', 'color': 'blue', 'material': 'softshell'} to {'piece count': '4-piece', 'color': 'red', 'material': 'hardshell'}; via paypal_4820484. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W3525030", "reason": "no longer needed"},
            ),
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W4866703",
                    "address1": "953 Park Avenue",
                    "address2": "Suite 613",
                    "city": "New York",
                    "country": "USA",
                    "state": "NY",
                    "zip": "10064",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W4866703",
                    "item_ids": ["8142779083", "8426249116", "1793929609"],
                    "new_item_ids": ["5268233322", "4648362606", "1071497737"],
                    "payment_method_id": "paypal_4820484",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W9677982", "reason": "no longer needed"},
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W2912646",
                    "item_ids": ["1096508426", "6301799585"],
                    "new_item_ids": ["9237024510", "9956648681"],
                    "payment_method_id": "paypal_4820484",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="aarav_moore_6923",
        instruction="Your name is Aarav Moore and your zip code is 85041. You are independent, rigid, creative, confident. Return #W8496475 via paypal_4751854: Tea Kettle; Headphones; Perfume; Water Bottle; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W8496475",
                    "item_ids": [
                        "7274158061",
                        "9314474252",
                        "6826843914",
                        "3229676465",
                    ],
                    "payment_method_id": "paypal_4751854",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="harper_kovacs_9747",
        instruction="Your name is Harper Kovacs and your zip code is 10206. You are busy, independent, happy, direct. Return #W6221400 via gift_card_5087631: Air Purifier; Water Bottle; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W6221400",
                    "item_ids": ["4035304400", "7843064651"],
                    "payment_method_id": "gift_card_5087631",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lucas_martin_7509",
        instruction="Your name is Lucas Martin and your email is lucas.martin9430@example.com. You are logical, impatient. Cancel order #W5502903 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W5502903", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="emma_santos_9753",
        instruction="Your name is Emma Santos and your zip code is 78228. You are creative, sad, pessimistic, impatient, busy. For #W1539823, exchange Smart Watch {'color': 'black', 'band material': 'silicone', 'display': 'LCD'} to {'color': 'gold', 'display': 'AMOLED'}; via gift_card_6023546. Cancel order #W1620235 because ordered by mistake. Cancel order #W9903153 because ordered by mistake. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W1539823",
                    "item_ids": ["2860956907"],
                    "new_item_ids": ["2681513500"],
                    "payment_method_id": "gift_card_6023546",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W1620235", "reason": "ordered by mistake"},
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W9903153", "reason": "ordered by mistake"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="fatima_anderson_7445",
        instruction="Your name is Fatima Anderson and your zip code is 78786. You are pessimistic, rigid, sad, shy, messy. For #W6368178, change payment to gift_card_8070316. For #W6368178, modify Electric Kettle {'capacity': '1L', 'material': 'plastic', 'color': 'white'} to {'capacity': '1.5L'}; via gift_card_8070316. ",
        actions=[
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W6368178",
                    "payment_method_id": "gift_card_8070316",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6368178",
                    "item_ids": ["2243454707"],
                    "new_item_ids": ["2698416822"],
                    "payment_method_id": "gift_card_8070316",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="amelia_ito_8772",
        instruction="Your name is Amelia Ito and your zip code is 32184. You are flexible, sad, logical, direct. For #W3733909, exchange Bicycle {'frame size': 'medium', 'color': 'black', 'type': 'mountain'} to {'color': 'green', 'type': 'road'}; Coffee Maker {'color': 'black', 'capacity': '2 cups', 'type': 'espresso', 'features': 'timer'} to {'color': 'stainless steel', 'capacity': '4 cups', 'type': 'drip', 'features': 'auto shutoff'}; via paypal_2767694. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W3733909",
                    "item_ids": ["2143041831", "9862136885"],
                    "new_item_ids": ["7758198585", "3039787582"],
                    "payment_method_id": "paypal_2767694",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="chen_silva_7485",
        instruction="Your name is Chen Silva and your zip code is 46281. You are messy, optimistic, insecure, cautious. For #W9571698, exchange Coffee Maker {'color': 'black', 'capacity': '4 cups', 'type': 'espresso', 'features': 'timer'} to {'capacity': '1 cup', 'type': 'french press', 'features': 'auto shutoff'}; via gift_card_7250692. Return #W3069600 via credit_card_1565124: Skateboard; Return #W2598834 via gift_card_7250692: Jigsaw Puzzle; ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W9571698",
                    "item_ids": ["5952720925"],
                    "new_item_ids": ["3020722515"],
                    "payment_method_id": "gift_card_7250692",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W3069600",
                    "item_ids": ["4545791457"],
                    "payment_method_id": "credit_card_1565124",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W2598834",
                    "item_ids": ["6245746168"],
                    "payment_method_id": "gift_card_7250692",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="chen_johnson_4204",
        instruction="Your name is Chen Johnson and your email is chen.johnson3889@example.com. You are pessimistic, polite, patient, organized, creative. For #W5061109, modify Bluetooth Speaker {'color': 'blue', 'battery life': '20 hours', 'water resistance': 'yes'} to {'color': 'green', 'water resistance': 'no'}; via paypal_3742148. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W5061109",
                    "item_ids": ["3254583681"],
                    "new_item_ids": ["9440686670"],
                    "payment_method_id": "paypal_3742148",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lei_li_6575",
        instruction="Your name is Lei Li and your zip code is 85033. You are outgoing, rigid. For #W3414433, modify Digital Camera {'resolution': '30MP', 'zoom': '3x', 'storage': 'SD card'} to {'resolution': '20MP'}; Electric Kettle {'capacity': '1L', 'material': 'stainless steel', 'color': 'black'} to {'material': 'glass'}; via gift_card_8049813. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W3414433",
                    "item_ids": ["1804581713", "7602931732"],
                    "new_item_ids": ["8363011723", "2323972008"],
                    "payment_method_id": "gift_card_8049813",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ava_kovacs_3448",
        instruction="Your name is Ava Kovacs and your email is ava.kovacs4827@example.com. You are pessimistic, relaxing. Cancel order #W4184032 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W4184032", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_thomas_1791",
        instruction="Your name is Ethan Thomas and your email is ethan.thomas7730@example.com. You are direct, outgoing, impatient. Return #W7764382 via gift_card_2519457: Mechanical Keyboard; Pet Bed; Indoor Security Camera; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W7764382",
                    "item_ids": ["9665000388", "5067898160", "3909704820"],
                    "payment_method_id": "gift_card_2519457",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="chen_anderson_8078",
        instruction="Your name is Chen Anderson and your email is chen.anderson4495@example.com. You are dependent, insecure, organized, impatient. Return #W5332101 via gift_card_3434432: T-Shirt; Cancel order #W1348788 because no longer needed. ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W5332101",
                    "item_ids": ["1176194968"],
                    "payment_method_id": "gift_card_3434432",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W1348788", "reason": "no longer needed"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_lopez_6291",
        instruction="Your name is Ethan Lopez and your email is ethan.lopez8943@example.com. You are cautious, relaxing. For #W8073920, modify Hiking Boots {'size': '12', 'material': 'leather', 'waterproof': 'yes'} to {'size': '7', 'material': 'synthetic', 'waterproof': 'no'}; via gift_card_7219486. Cancel order #W6779827 because no longer needed. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W8073920",
                    "item_ids": ["8277474082"],
                    "new_item_ids": ["1437889264"],
                    "payment_method_id": "gift_card_7219486",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W6779827", "reason": "no longer needed"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mia_jackson_5377",
        instruction="Your name is Mia Jackson and your email is mia.jackson2679@example.com. You are impatient, creative, relaxing. Cancel order #W1298962 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W1298962", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="emma_kovacs_7176",
        instruction="Your name is Emma Kovacs and your zip code is 32254. You are happy, rigid, creative, polite. For #W2307204, modify Notebook {'size': 'A6', 'cover type': 'soft cover'} to {'size': 'A4', 'cover type': 'hard cover'}; via paypal_1038468. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W2307204",
                    "item_ids": ["9421195098"],
                    "new_item_ids": ["1199058591"],
                    "payment_method_id": "paypal_1038468",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="raj_kovacs_9859",
        instruction="Your name is Raj Kovacs and your email is raj.kovacs2291@example.com. You are outgoing, independent, messy. For #W1473345, exchange Coffee Maker {'color': 'black', 'capacity': '1 cup', 'type': 'french press', 'features': 'auto shutoff'} to {'capacity': '2 cups', 'type': 'espresso', 'features': 'timer'}; via paypal_7525649. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W1473345",
                    "item_ids": ["3020722515"],
                    "new_item_ids": ["9862136885"],
                    "payment_method_id": "paypal_7525649",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lei_ahmed_1705",
        instruction="Your name is Lei Ahmed and your email is lei.ahmed1696@example.com. You are pessimistic, organized. Cancel order #W9132840 because ordered by mistake. Cancel order #W3931703 because ordered by mistake. For #W6724985, modify Water Bottle {'capacity': '500ml', 'material': 'stainless steel', 'color': 'green'} to {'material': 'plastic', 'color': 'black'}; via credit_card_3593714. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W9132840", "reason": "ordered by mistake"},
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W3931703", "reason": "ordered by mistake"},
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6724985",
                    "item_ids": ["7533802601"],
                    "new_item_ids": ["3229676465"],
                    "payment_method_id": "credit_card_3593714",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="anya_garcia_3271",
        instruction="Your name is Anya Garcia and your zip code is 19036. You are dependent, cautious. Cancel order #W6436609 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W6436609", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="isabella_santos_1643",
        instruction="Your name is Isabella Santos and your email is isabella.santos9317@example.com. You are dependent, sad. Return #W1654332 via credit_card_4056740: Mechanical Keyboard; For #W9527030, modify Smart Watch {'color': 'gold', 'band material': 'leather', 'display': 'LCD'} to {}; via credit_card_4056740. ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W1654332",
                    "item_ids": ["9665000388"],
                    "payment_method_id": "credit_card_4056740",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W9527030",
                    "item_ids": ["9408160950"],
                    "new_item_ids": ["9408160950"],
                    "payment_method_id": "credit_card_4056740",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="chen_johnson_4204",
        instruction="Your name is Chen Johnson and your email is chen.johnson3889@example.com. You are patient, happy, messy, independent, cautious. For #W5061109, modify Bluetooth Speaker {'color': 'blue', 'battery life': '20 hours', 'water resistance': 'yes'} to {}; Office Chair {'material': 'fabric', 'color': 'blue', 'armrest': 'adjustable', 'backrest height': 'standard'} to {'color': 'black', 'armrest': 'fixed'}; Makeup Kit {'skin tone': 'dark', 'kit size': 'basic', 'brand': 'Brand B'} to {'kit size': 'professional'}; via paypal_3742148. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W5061109",
                    "item_ids": ["3254583681", "8323284863", "6254646215"],
                    "new_item_ids": ["3254583681", "8426249116", "5012998807"],
                    "payment_method_id": "paypal_3742148",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sophia_wilson_7936",
        instruction="Your name is Sophia Wilson and your zip code is 78775. You are direct, creative, relaxing, independent. For #W8209112, exchange Laptop {'screen size': '13-inch', 'processor': 'i7', 'ram': '32GB', 'storage': '256GB SSD', 'color': 'space grey'} to {'screen size': '15-inch', 'processor': 'i5'}; via credit_card_6428848. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W8209112",
                    "item_ids": ["8997785118"],
                    "new_item_ids": ["2216662955"],
                    "payment_method_id": "credit_card_6428848",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="aarav_gonzalez_5113",
        instruction="Your name is Aarav Gonzalez and your email is aarav.gonzalez9269@example.com. You are direct, pessimistic, shy, dependent. For #W9160732, modify Bluetooth Speaker {'color': 'black', 'battery life': '10 hours', 'water resistance': 'no'} to {'color': 'blue'}; via gift_card_5979071. Return #W6797115 via gift_card_5979071: Air Purifier; Mechanical Keyboard; ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W9160732",
                    "item_ids": ["7597543861"],
                    "new_item_ids": ["6704763132"],
                    "payment_method_id": "gift_card_5979071",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W6797115",
                    "item_ids": ["8302289002", "7658724607"],
                    "payment_method_id": "gift_card_5979071",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ava_kovacs_3448",
        instruction="Your name is Ava Kovacs and your email is ava.kovacs4827@example.com. You are relaxing, polite, patient, organized. For #W6344370, exchange Skateboard {'deck material': 'plastic', 'length': '28 inch', 'design': 'plain'} to {'deck material': 'bamboo', 'length': '34 inch', 'design': 'custom'}; via paypal_7443913. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W6344370",
                    "item_ids": ["4545791457"],
                    "new_item_ids": ["6956751343"],
                    "payment_method_id": "paypal_7443913",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="evelyn_lopez_5487",
        instruction="Your name is Evelyn Lopez and your email is evelyn.lopez6910@example.com. You are logical, patient, optimistic, shy, rigid. Cancel order #W1890669 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W1890669", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mia_thomas_4629",
        instruction="Your name is Mia Thomas and your zip code is 60654. You are outgoing, busy, rigid, confident. Cancel order #W5208989 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W5208989", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_ahmed_6778",
        instruction="Your name is Olivia Ahmed and your email is olivia.ahmed5620@example.com. You are organized, happy, creative. Return #W1579621 via credit_card_9698900: Water Bottle; Mechanical Keyboard; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W1579621",
                    "item_ids": ["4579334072", "6439196450"],
                    "payment_method_id": "credit_card_9698900",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="liam_thomas_7882",
        instruction="Your name is Liam Thomas and your zip code is 85049. You are organized, polite, flexible, busy, cautious. Return #W6397299 via credit_card_3261838: Garden Hose; Return #W8488728 via paypal_3650980: Hiking Boots; For #W3295833, modify Skateboard {'deck material': 'bamboo', 'length': '31 inch', 'design': 'graphic'} to {'length': '28 inch', 'design': 'plain'}; via paypal_3650980. ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W6397299",
                    "item_ids": ["5206946487"],
                    "payment_method_id": "credit_card_3261838",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W8488728",
                    "item_ids": ["5676696062"],
                    "payment_method_id": "paypal_3650980",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W3295833",
                    "item_ids": ["5312063289"],
                    "new_item_ids": ["8176740019"],
                    "payment_method_id": "paypal_3650980",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="raj_moore_7909",
        instruction="Your name is Raj Moore and your zip code is 20566. You are curious, messy. For #W9929926, modify Bluetooth Speaker {'color': 'blue', 'battery life': '10 hours', 'water resistance': 'yes'} to {'water resistance': 'no'}; via gift_card_6009199. For #W3467101, exchange Smart Watch {'color': 'black', 'band material': 'silicone', 'display': 'LCD'} to {'color': 'gold', 'band material': 'leather'}; via gift_card_6009199. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W9929926",
                    "item_ids": ["4716977452"],
                    "new_item_ids": ["6704763132"],
                    "payment_method_id": "gift_card_6009199",
                },
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W3467101",
                    "item_ids": ["2860956907"],
                    "new_item_ids": ["9408160950"],
                    "payment_method_id": "gift_card_6009199",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="fatima_li_5040",
        instruction="Your name is Fatima Li and your email is fatima.li1185@example.com. You are logical, sad, organized. Cancel order #W8005719 because no longer needed. For #W3510092, change payment to paypal_6366157. For #W3510092, modify Laptop {'screen size': '13-inch', 'processor': 'i5', 'ram': '16GB', 'storage': '512GB SSD', 'color': 'space grey'} to {'processor': 'i7', 'ram': '32GB', 'color': 'black'}; via credit_card_2713802. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W8005719", "reason": "no longer needed"},
            ),
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W3510092",
                    "payment_method_id": "paypal_6366157",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W3510092",
                    "item_ids": ["6056040996"],
                    "new_item_ids": ["1657832319"],
                    "payment_method_id": "credit_card_2713802",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="liam_johnson_5676",
        instruction="Your name is Liam Johnson and your zip code is 46244. You are messy, pessimistic, relaxing. Return #W7190291 via credit_card_7120747: Headphones; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W7190291",
                    "item_ids": ["7184044281"],
                    "payment_method_id": "credit_card_7120747",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yara_davis_8348",
        instruction="Your name is Yara Davis and your zip code is 92122. You are curious, logical, insecure. Return #W3952055 via credit_card_1248375: Dumbbell Set; Makeup Kit; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W3952055",
                    "item_ids": ["3333391894", "7902309762"],
                    "payment_method_id": "credit_card_1248375",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="noah_kovacs_1216",
        instruction="Your name is Noah Kovacs and your zip code is 20566. You are patient, dependent, cautious, creative, relaxing. Cancel order #W9440076 because ordered by mistake. For #W3002300, exchange Bluetooth Speaker {'color': 'green', 'battery life': '10 hours', 'water resistance': 'no'} to {'color': 'red'}; via gift_card_2486551. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W9440076", "reason": "ordered by mistake"},
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W3002300",
                    "item_ids": ["9179378709"],
                    "new_item_ids": ["1689914594"],
                    "payment_method_id": "gift_card_2486551",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="liam_li_5260",
        instruction="Your name is Liam Li and your zip code is 94120. You are happy, busy, direct, independent, impatient. Cancel order #W9653558 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W9653558", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_ahmed_6232",
        instruction="Your name is Yusuf Ahmed and your email is yusuf.ahmed5476@example.com. You are messy, confident, busy, direct. For #W7007896, modify Laptop {'screen size': '13-inch', 'processor': 'i9', 'ram': '8GB', 'storage': '1TB SSD', 'color': 'space grey'} to {'processor': 'i5', 'ram': '16GB', 'storage': '512GB SSD'}; via credit_card_2167533. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W7007896",
                    "item_ids": ["8193934556"],
                    "new_item_ids": ["6056040996"],
                    "payment_method_id": "credit_card_2167533",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="omar_muller_8833",
        instruction="Your name is Omar Muller and your email is omar.muller2208@example.com. You are logical, rigid, sad, direct. For #W9941744, exchange Tablet {'screen size': '7-inch', 'storage': '32GB', 'color': 'gold'} to {'storage': '128GB', 'color': 'black'}; Bluetooth Speaker {'color': 'red', 'battery life': '10 hours', 'water resistance': 'no'} to {'color': 'blue', 'water resistance': 'yes'}; via paypal_4439305. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W9941744",
                    "item_ids": ["6501071631", "1689914594"],
                    "new_item_ids": ["4913411651", "4716977452"],
                    "payment_method_id": "paypal_4439305",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yara_santos_1202",
        instruction="Your name is Yara Santos and your zip code is 91163. You are pessimistic, creative. Return #W3232025 via gift_card_4543462: Dumbbell Set; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W3232025",
                    "item_ids": ["2444431651"],
                    "payment_method_id": "gift_card_4543462",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lucas_silva_7435",
        instruction="Your name is Lucas Silva and your email is lucas.silva5146@example.com. You are rigid, sad, cautious. Cancel order #W1814268 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W1814268", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_brown_4616",
        instruction="Your name is Olivia Brown and your zip code is 43118. You are pessimistic, outgoing, direct. For #W2912153, exchange Desk Lamp {'color': 'white', 'brightness': 'high', 'power source': 'battery'} to {'color': 'silver', 'brightness': 'low', 'power source': 'AC adapter'}; via credit_card_3081930. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W2912153",
                    "item_ids": ["1270145486"],
                    "new_item_ids": ["1569765161"],
                    "payment_method_id": "credit_card_3081930",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mia_thomas_4629",
        instruction="Your name is Mia Thomas and your zip code is 60654. You are independent, confident. Return #W6872071 via paypal_2977884: Bluetooth Speaker; LED Light Bulb; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W6872071",
                    "item_ids": ["4716977452", "7445824652"],
                    "payment_method_id": "paypal_2977884",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_lopez_3865",
        instruction="Your name is Olivia Lopez and your email is olivia.lopez4535@example.com. You are happy, organized, curious. For #W7449508, exchange Sneakers {'size': '6', 'color': 'black', 'material': 'synthetic'} to {}; Espresso Machine {'pressure': '19 bar', 'capacity': '1L', 'type': 'capsule'} to {'capacity': '2L'}; via gift_card_7711863. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W7449508",
                    "item_ids": ["6477915553", "6200867091"],
                    "new_item_ids": ["6477915553", "1157853815"],
                    "payment_method_id": "gift_card_7711863",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="harper_thomas_9402",
        instruction="Your name is Harper Thomas and your zip code is 90891. You are messy, logical, sad, optimistic. Cancel order #W7425646 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W7425646", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yara_silva_7567",
        instruction="Your name is Yara Silva and your zip code is 77159. You are dependent, relaxing, creative. For #W9810810, modify Wristwatch {'strap material': 'leather', 'dial color': 'white'} to {}; Electric Kettle {'capacity': '1.5L', 'material': 'plastic', 'color': 'white'} to {'capacity': '2L', 'material': 'glass'}; via gift_card_7252880. Return #W3964602 via gift_card_7252880: Cycling Helmet {'size': 'L', 'color': 'blue', 'ventilation': 'low'}; Dumbbell Set; Cycling Helmet {'size': 'S', 'color': 'black', 'ventilation': 'medium'}; Cancel order #W3730488 because no longer needed. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W9810810",
                    "item_ids": ["1355937109", "2698416822"],
                    "new_item_ids": ["1355937109", "4064702754"],
                    "payment_method_id": "gift_card_7252880",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W3964602",
                    "item_ids": ["7907773809", "4422467033", "5537798301"],
                    "payment_method_id": "gift_card_7252880",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W3730488", "reason": "no longer needed"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ivan_kim_7727",
        instruction="Your name is Ivan Kim and your zip code is 60636. You are messy, happy, polite, relaxing, optimistic. Cancel order #W6443279 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W6443279", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="james_kim_7213",
        instruction="Your name is James Kim and your zip code is 92199. You are curious, patient, shy, dependent, organized. For #W9722559, change address to {'order_id': '#W9722559', 'address1': '320 Cedar Avenue', 'address2': 'Suite 116', 'city': 'San Antonio', 'country': 'USA', 'state': 'TX', 'zip': '78219'} (same as #W9154975). For #W9722559, modify Luggage Set {'piece count': '2-piece', 'color': 'red', 'material': 'hardshell'} to {'piece count': '3-piece', 'color': 'blue', 'material': 'softshell'}; via paypal_8963303. ",
        actions=[
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W9722559",
                    "address1": "320 Cedar Avenue",
                    "address2": "Suite 116",
                    "city": "San Antonio",
                    "country": "USA",
                    "state": "TX",
                    "zip": "78219",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W9722559",
                    "item_ids": ["8964750292"],
                    "new_item_ids": ["6301799585"],
                    "payment_method_id": "paypal_8963303",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lei_hernandez_8500",
        instruction="Your name is Lei Hernandez and your zip code is 43222. You are impatient, independent, confident. Return #W2982823 via gift_card_5245016: Cycling Helmet; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W2982823",
                    "item_ids": ["1719127154"],
                    "payment_method_id": "gift_card_5245016",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mei_gonzalez_4785",
        instruction="Your name is Mei Gonzalez and your zip code is 95170. You are patient, busy, polite. For #W2052757, modify Notebook {'size': 'A5', 'cover type': 'soft cover'} to {'size': 'A4'}; Office Chair {'material': 'mesh', 'color': 'red', 'armrest': 'none', 'backrest height': 'standard'} to {'color': 'gray', 'armrest': 'fixed', 'backrest height': 'high-back'}; via credit_card_4387170. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W2052757",
                    "item_ids": ["9799386954", "4274709903"],
                    "new_item_ids": ["7579176349", "2386562819"],
                    "payment_method_id": "credit_card_4387170",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="daiki_khan_6856",
        instruction="Your name is Daiki Khan and your email is daiki.khan2146@example.com. You are shy, sad, dependent, confident, organized. For #W8461477, modify Action Camera {'resolution': '1080p', 'waterproof': 'no', 'color': 'silver'} to {'resolution': '4K', 'waterproof': 'yes'}; via gift_card_2491643. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W8461477",
                    "item_ids": ["1810466394"],
                    "new_item_ids": ["6117189161"],
                    "payment_method_id": "gift_card_2491643",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sophia_jackson_6355",
        instruction="Your name is Sophia Jackson and your email is sophia.jackson1954@example.com. You are confident, shy, cautious, flexible. For #W6977171, exchange Mechanical Keyboard {'switch type': 'linear', 'backlight': 'RGB', 'size': 'full size'} to {'size': '80%'}; via credit_card_8041020. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W6977171",
                    "item_ids": ["1151293680"],
                    "new_item_ids": ["8484921793"],
                    "payment_method_id": "credit_card_8041020",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sofia_li_8235",
        instruction="Your name is Sofia Li and your zip code is 75390. You are flexible, organized, relaxing. For #W6599568, change payment to credit_card_8296913. For #W6599568, modify Bluetooth Speaker {'color': 'red', 'battery life': '20 hours', 'water resistance': 'no'} to {'color': 'blue'}; via credit_card_8296913. ",
        actions=[
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W6599568",
                    "payment_method_id": "credit_card_8296913",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6599568",
                    "item_ids": ["1052700637"],
                    "new_item_ids": ["2635605237"],
                    "payment_method_id": "credit_card_8296913",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_ito_3591",
        instruction="Your name is Olivia Ito and your zip code is 80218. You are independent, rigid. Cancel order #W3657213 because no longer needed. For #W5442520, modify Gaming Mouse {'color': 'black', 'sensor type': 'optical', 'connectivity': 'wired'} to {'sensor type': 'laser'}; via credit_card_9753331. For #W5866402, exchange Espresso Machine {'pressure': '19 bar', 'capacity': '1L', 'type': 'automatic'} to {'pressure': '9 bar', 'type': 'capsule'}; Sneakers {'size': '11', 'color': 'black', 'material': 'synthetic'} to {'size': '10', 'color': 'gray', 'material': 'leather'}; via paypal_8049766. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W3657213", "reason": "no longer needed"},
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W5442520",
                    "item_ids": ["3330317167"],
                    "new_item_ids": ["2193628750"],
                    "payment_method_id": "credit_card_9753331",
                },
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W5866402",
                    "item_ids": ["6242772310", "9727387530"],
                    "new_item_ids": ["7806008610", "2509076505"],
                    "payment_method_id": "paypal_8049766",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="raj_lopez_5873",
        instruction="Your name is Raj Lopez and your email is raj.lopez2997@example.com. You are relaxing, messy, happy. Cancel order #W3502364 because no longer needed. Cancel order #W5107138 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W3502364", "reason": "no longer needed"},
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W5107138", "reason": "no longer needed"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="amelia_gonzalez_4098",
        instruction="Your name is Amelia Gonzalez and your email is amelia.gonzalez4271@example.com. You are outgoing, relaxing. For #W1762492, exchange Hiking Boots {'size': '10', 'material': 'synthetic', 'waterproof': 'no'} to {'size': '8'}; via gift_card_2611937. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W1762492",
                    "item_ids": ["4127323219"],
                    "new_item_ids": ["3613716226"],
                    "payment_method_id": "gift_card_2611937",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ava_johnson_5052",
        instruction="Your name is Ava Johnson and your zip code is 92171. You are relaxing, insecure, creative, independent. Return #W9178204 via paypal_3846161: Desk Lamp; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W9178204",
                    "item_ids": ["6805564527"],
                    "payment_method_id": "paypal_3846161",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="raj_davis_2615",
        instruction="Your name is Raj Davis and your email is raj.davis3587@example.com. You are busy, patient, dependent, messy, sad. Return #W5463717 via gift_card_8006222: Grill; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W5463717",
                    "item_ids": ["6589665742"],
                    "payment_method_id": "gift_card_8006222",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sophia_jackson_6355",
        instruction="Your name is Sophia Jackson and your zip code is 60651. You are logical, busy, optimistic, happy, polite. For #W6977171, exchange Jigsaw Puzzle {'pieces': '1000', 'theme': 'art', 'difficulty level': 'expert'} to {'pieces': '1500', 'difficulty level': 'intermediate'}; via paypal_7425862. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W6977171",
                    "item_ids": ["9370300555"],
                    "new_item_ids": ["5546244844"],
                    "payment_method_id": "paypal_7425862",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="liam_kovacs_4286",
        instruction="Your name is Liam Kovacs and your email is liam.kovacs5432@example.com. You are cautious, polite. Cancel order #W5762451 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W5762451", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ava_nguyen_6646",
        instruction="Your name is Ava Nguyen and your zip code is 94128. You are outgoing, happy, direct. Cancel order #W6272294 because no longer needed. For #W9232383, modify Headphones {'type': 'on-ear', 'connectivity': 'wireless', 'color': 'white'} to {}; via credit_card_5683823. Return #W8668939 via credit_card_5683823: Grill {'type': 'electric', 'size': 'medium', 'features': 'rotisserie'}; Water Bottle; Grill {'type': 'electric', 'size': 'portable', 'features': 'none'}; For #W1242543, modify Skateboard {'deck material': 'plastic', 'length': '34 inch', 'design': 'custom'} to {'length': '31 inch'}; via gift_card_1994993. For #W8367380, modify Dumbbell Set {'weight range': '55-75 lbs', 'material': 'iron', 'set type': 'fixed'} to {'weight range': '5-25 lbs', 'material': 'rubber', 'set type': 'adjustable'}; Bluetooth Speaker {'color': 'red', 'battery life': '10 hours', 'water resistance': 'no'} to {'color': 'blue', 'water resistance': 'yes'}; Fleece Jacket {'size': 'L', 'color': 'red', 'zipper': 'half'} to {'size': 'XL', 'color': 'navy', 'zipper': 'full'}; via gift_card_1994993. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W6272294", "reason": "no longer needed"},
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W9232383",
                    "item_ids": ["9805150490"],
                    "new_item_ids": ["9805150490"],
                    "payment_method_id": "credit_card_5683823",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W8668939",
                    "item_ids": ["7717598293", "7199146548", "1120917161"],
                    "payment_method_id": "credit_card_5683823",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W1242543",
                    "item_ids": ["9594745976"],
                    "new_item_ids": ["5038485381"],
                    "payment_method_id": "gift_card_1994993",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W8367380",
                    "item_ids": ["2444431651", "1689914594", "8733974883"],
                    "new_item_ids": ["7896397433", "4716977452", "7528037711"],
                    "payment_method_id": "gift_card_1994993",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_silva_7273",
        instruction="Your name is Olivia Silva and your zip code is 32240. You are patient, flexible, organized, optimistic, cautious. For #W7613749, modify Wall Clock {'diameter': '12 inches', 'color': 'white', 'type': 'analog'} to {'diameter': '10 inches', 'color': 'wood'}; Smartphone {'color': 'rose gold', 'storage': '64GB', 'RAM': '8GB', 'screen size': '5.8-inch'} to {'color': 'black', 'storage': '128GB'}; via paypal_9379149. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W7613749",
                    "item_ids": ["6508153405", "5311660992"],
                    "new_item_ids": ["6534134392", "1507389580"],
                    "payment_method_id": "paypal_9379149",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_jackson_7865",
        instruction="Your name is Yusuf Jackson and your email is yusuf.jackson4654@example.com. You are outgoing, organized, polite, confident, curious. For #W7128968, exchange Pet Bed {'size': 'large', 'material': 'polyester', 'color': 'brown'} to {'color': 'grey'}; Vacuum Cleaner {'type': 'robotic', 'bagged/bagless': 'bagged', 'features': 'pet hair removal'} to {'type': 'canister'}; via gift_card_7037673. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W7128968",
                    "item_ids": ["7729002517", "6259501109"],
                    "new_item_ids": ["7917269097", "2872451762"],
                    "payment_method_id": "gift_card_7037673",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yara_lee_7701",
        instruction="Your name is Yara Lee and your zip code is 77243. You are pessimistic, insecure, rigid, outgoing, direct. For #W3320020, modify Office Chair {'material': 'leather', 'color': 'red', 'armrest': 'none', 'backrest height': 'high-back'} to {'material': 'mesh', 'color': 'blue', 'armrest': 'fixed', 'backrest height': 'standard'}; via credit_card_6680679. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W3320020",
                    "item_ids": ["3609437808"],
                    "new_item_ids": ["3704016729"],
                    "payment_method_id": "credit_card_6680679",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="chen_anderson_8078",
        instruction="Your name is Chen Anderson and your email is chen.anderson4495@example.com. You are independent, cautious. For #W1701126, exchange Makeup Kit {'skin tone': 'light', 'kit size': 'professional', 'brand': 'Brand B'} to {'skin tone': 'medium', 'brand': 'Brand A'}; via credit_card_9389219. Cancel order #W1348788 because no longer needed. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W1701126",
                    "item_ids": ["7902309762"],
                    "new_item_ids": ["2882812427"],
                    "payment_method_id": "credit_card_9389219",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W1348788", "reason": "no longer needed"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_ahmed_6778",
        instruction="Your name is Olivia Ahmed and your zip code is 94152. You are polite, outgoing. For #W2260828, exchange Mechanical Keyboard {'switch type': 'tactile', 'backlight': 'none', 'size': 'full size'} to {'switch type': 'linear', 'backlight': 'RGB'}; via credit_card_9698900. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W2260828",
                    "item_ids": ["1340995114"],
                    "new_item_ids": ["1151293680"],
                    "payment_method_id": "credit_card_9698900",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_ahmed_6778",
        instruction="Your name is Olivia Ahmed and your zip code is 94152. You are happy, outgoing. For #W3972714, exchange Hiking Boots {'size': '9', 'material': 'synthetic', 'waterproof': 'yes'} to {'size': '11', 'material': 'leather', 'waterproof': 'no'}; via gift_card_1044904. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W3972714",
                    "item_ids": ["2658930189"],
                    "new_item_ids": ["5676696062"],
                    "payment_method_id": "gift_card_1044904",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="omar_silva_7446",
        instruction="Your name is Omar Silva and your email is omar.silva4147@example.com. You are confident, logical, happy. For #W9673784, modify Espresso Machine {'pressure': '19 bar', 'capacity': '1L', 'type': 'manual'} to {'pressure': '15 bar'}; via paypal_2192303. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W9673784",
                    "item_ids": ["9884666842"],
                    "new_item_ids": ["3714494375"],
                    "payment_method_id": "paypal_2192303",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="chen_lopez_3345",
        instruction="Your name is Chen Lopez and your email is chen.lopez1681@example.com. You are independent, optimistic, creative, patient, confident. Cancel order #W1790752 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W1790752", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="aarav_davis_4756",
        instruction="Your name is Aarav Davis and your email is aarav.davis1165@example.com. You are organized, patient, independent, logical. For #W3196599, change address to {'order_id': '#W3196599', 'address1': '178 Lakeview Drive', 'address2': 'Suite 576', 'city': 'Fort Worth', 'country': 'USA', 'state': 'TX', 'zip': '76150'} (same as #W7430166). For #W3196599, modify Dumbbell Set {'weight range': '30-50 lbs', 'material': 'rubber', 'set type': 'fixed'} to {'weight range': '55-75 lbs', 'material': 'iron'}; via gift_card_9708163. For #W7430166, change address to {'order_id': '#W7430166', 'address1': '808 Chestnut Street', 'address2': 'Suite 832', 'city': 'Phoenix', 'country': 'USA', 'state': 'AZ', 'zip': '85072'} (same as #W2403075). For #W7430166, modify Electric Kettle {'capacity': '1L', 'material': 'glass', 'color': 'silver'} to {'color': 'white'}; via gift_card_9708163. ",
        actions=[
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W3196599",
                    "address1": "178 Lakeview Drive",
                    "address2": "Suite 576",
                    "city": "Fort Worth",
                    "country": "USA",
                    "state": "TX",
                    "zip": "76150",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W3196599",
                    "item_ids": ["6171242004"],
                    "new_item_ids": ["2444431651"],
                    "payment_method_id": "gift_card_9708163",
                },
            ),
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W7430166",
                    "address1": "808 Chestnut Street",
                    "address2": "Suite 832",
                    "city": "Phoenix",
                    "country": "USA",
                    "state": "AZ",
                    "zip": "85072",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W7430166",
                    "item_ids": ["1240311797"],
                    "new_item_ids": ["5268233322"],
                    "payment_method_id": "gift_card_9708163",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mei_moore_8248",
        instruction="Your name is Mei Moore and your email is mei.moore6624@example.com. You are rigid, relaxing. For #W9694847, exchange Air Purifier {'room size': 'small', 'filter type': 'ionic', 'features': 'quiet operation'} to {'room size': 'medium', 'filter type': 'HEPA', 'features': 'night mode'}; via credit_card_2902980. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W9694847",
                    "item_ids": ["5669664287"],
                    "new_item_ids": ["1327854740"],
                    "payment_method_id": "credit_card_2902980",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="james_lee_5010",
        instruction="Your name is James Lee and your zip code is 95161. You are busy, polite, cautious, impatient, insecure. For #W5356919, modify Jigsaw Puzzle {'pieces': '1000', 'theme': 'art', 'difficulty level': 'expert'} to {'pieces': '500', 'difficulty level': 'intermediate'}; via paypal_2684483. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W5356919",
                    "item_ids": ["9370300555"],
                    "new_item_ids": ["4068787148"],
                    "payment_method_id": "paypal_2684483",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ivan_santos_6635",
        instruction="Your name is Ivan Santos and your email is ivan.santos3158@example.com. You are confident, sad. Cancel order #W3913498 because ordered by mistake. Cancel order #W8770097 because no longer needed. Cancel order #W5183325 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W3913498", "reason": "ordered by mistake"},
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W8770097", "reason": "no longer needed"},
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W5183325", "reason": "no longer needed"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="liam_santos_5468",
        instruction="Your name is Liam Santos and your zip code is 78762. You are polite, organized. For #W6794581, change address to {'order_id': '#W6794581', 'address1': '441 Hillcrest Drive', 'address2': 'Suite 386', 'city': 'Austin', 'country': 'USA', 'state': 'TX', 'zip': '78762'} (same as #W4011814). For #W6794581, modify Tea Kettle {'material': 'stainless steel', 'capacity': '2 liters', 'stovetop compatibility': 'induction'} to {'material': 'glass', 'capacity': '1 liter', 'stovetop compatibility': 'gas'}; Cycling Helmet {'size': 'M', 'color': 'red', 'ventilation': 'medium'} to {'size': 'L', 'color': 'black', 'ventilation': 'high'}; via credit_card_1055108. ",
        actions=[
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W6794581",
                    "address1": "441 Hillcrest Drive",
                    "address2": "Suite 386",
                    "city": "Austin",
                    "country": "USA",
                    "state": "TX",
                    "zip": "78762",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6794581",
                    "item_ids": ["1906487464", "1719127154"],
                    "new_item_ids": ["3909406921", "1665571435"],
                    "payment_method_id": "credit_card_1055108",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="omar_kim_3528",
        instruction="Your name is Omar Kim and your zip code is 32214. You are busy, happy, optimistic. For #W7111824, modify Espresso Machine {'pressure': '19 bar', 'capacity': '1L', 'type': 'manual'} to {'pressure': '9 bar', 'capacity': '2L'}; via credit_card_3577130. For #W1080318, change payment to gift_card_3749819. For #W1080318, modify T-Shirt {'color': 'blue', 'size': 'S', 'material': 'cotton', 'style': 'v-neck'} to {'color': 'black', 'size': 'XL', 'style': 'crew neck'}; via gift_card_3749819. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W7111824",
                    "item_ids": ["9884666842"],
                    "new_item_ids": ["7774234341"],
                    "payment_method_id": "credit_card_3577130",
                },
            ),
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W1080318",
                    "payment_method_id": "gift_card_3749819",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W1080318",
                    "item_ids": ["8349118980"],
                    "new_item_ids": ["2060066974"],
                    "payment_method_id": "gift_card_3749819",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="harper_khan_8862",
        instruction="Your name is Harper Khan and your zip code is 85063. You are logical, organized, shy, curious, happy. Cancel order #W4725115 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W4725115", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="isabella_taylor_7478",
        instruction="Your name is Isabella Taylor and your zip code is 60646. You are creative, cautious, outgoing, insecure, rigid. For #W6717215, exchange Portable Charger {'capacity': '5000mAh', 'output': 'USB-C', 'color': 'white'} to {}; via gift_card_5501047. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W6717215",
                    "item_ids": ["7866854614"],
                    "new_item_ids": ["7866854614"],
                    "payment_method_id": "gift_card_5501047",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_lopez_9494",
        instruction="Your name is Olivia Lopez and your email is olivia.lopez8783@example.com. You are cautious, organized, creative, impatient, busy. For #W8955613, change payment to credit_card_6044108. For #W8955613, modify Backpack {'color': 'grey', 'size': 'large', 'material': 'polyester', 'compartment': 'hydration'} to {'color': 'green', 'size': 'small', 'compartment': 'camera'}; Smart Watch {'color': 'gold', 'band material': 'metal', 'display': 'AMOLED'} to {'band material': 'silicone'}; via credit_card_6044108. ",
        actions=[
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W8955613",
                    "payment_method_id": "credit_card_6044108",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W8955613",
                    "item_ids": ["6309044598", "2554056026"],
                    "new_item_ids": ["9851293632", "2681513500"],
                    "payment_method_id": "credit_card_6044108",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_lopez_9494",
        instruction="Your name is Olivia Lopez and your zip code is 92107. You are busy, sad, impatient, rigid. Cancel order #W8955613 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W8955613", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="isabella_santos_1643",
        instruction="Your name is Isabella Santos and your email is isabella.santos9317@example.com. You are optimistic, independent. Cancel order #W9667707 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W9667707", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mohamed_santos_2427",
        instruction="Your name is Mohamed Santos and your zip code is 76188. You are pessimistic, sad, shy, rigid. Return #W4840405 via gift_card_4710915: Luggage Set; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W4840405",
                    "item_ids": ["6301799585"],
                    "payment_method_id": "gift_card_4710915",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mei_gonzalez_4785",
        instruction="Your name is Mei Gonzalez and your email is mei.gonzalez8775@example.com. You are impatient, flexible, creative, pessimistic. For #W7303089, exchange Backpack {'color': 'navy', 'size': 'small', 'material': 'nylon', 'compartment': 'laptop'} to {'color': 'black', 'size': 'large', 'material': 'polyester'}; via credit_card_4387170. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W7303089",
                    "item_ids": ["2492465580"],
                    "new_item_ids": ["6906307980"],
                    "payment_method_id": "credit_card_4387170",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_kim_8860",
        instruction="Your name is Ethan Kim and your email is ethan.kim3231@example.com. You are rigid, cautious, polite, confident. Return #W1763367 via gift_card_5701566: Notebook; Cancel order #W8296441 because no longer needed. ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W1763367",
                    "item_ids": ["1199058591"],
                    "payment_method_id": "gift_card_5701566",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W8296441", "reason": "no longer needed"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sofia_hernandez_5364",
        instruction="Your name is Sofia Hernandez and your email is sofia.hernandez3039@example.com. You are optimistic, logical, flexible, outgoing, insecure. For #W3947049, exchange Cycling Helmet {'size': 'S', 'color': 'red', 'ventilation': 'low'} to {}; via credit_card_7901829. For #W6876713, exchange Vacuum Cleaner {'type': 'canister', 'bagged/bagless': 'bagged', 'features': 'cordless'} to {'bagged/bagless': 'bagless', 'features': 'pet hair removal'}; Espresso Machine {'pressure': '19 bar', 'capacity': '1L', 'type': 'capsule'} to {'pressure': '9 bar', 'capacity': '2L', 'type': 'manual'}; T-Shirt {'color': 'red', 'size': 'L', 'material': 'cotton', 'style': 'v-neck'} to {'color': 'purple', 'size': 'S', 'material': 'polyester'}; via credit_card_7901829. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W3947049",
                    "item_ids": ["3358616356"],
                    "new_item_ids": ["3358616356"],
                    "payment_method_id": "credit_card_7901829",
                },
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W6876713",
                    "item_ids": ["1345513440", "6200867091", "3234800602"],
                    "new_item_ids": ["7958300294", "7774234341", "9647292434"],
                    "payment_method_id": "credit_card_7901829",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="anya_brown_2024",
        instruction="Your name is Anya Brown and your zip code is 10121. You are insecure, optimistic, direct. For #W1430028, change address to {'order_id': '#W1430028', 'address1': '419 Main Street', 'address2': 'Suite 730', 'city': 'Dallas', 'country': 'USA', 'state': 'TX', 'zip': '75380'} (same as #W8883368). For #W1430028, change payment to credit_card_3414703. For #W1430028, modify Running Shoes {'size': '9', 'color': 'black', 'material': 'synthetic', 'sole': 'rubber'} to {'size': '8', 'color': 'red', 'material': 'leather', 'sole': 'EVA'}; Vacuum Cleaner {'type': 'robotic', 'bagged/bagless': 'bagless', 'features': 'pet hair removal'} to {'features': 'HEPA filter'}; via paypal_5206520. Return #W2922433 via credit_card_3414703: Grill; Tablet; ",
        actions=[
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W1430028",
                    "address1": "419 Main Street",
                    "address2": "Suite 730",
                    "city": "Dallas",
                    "country": "USA",
                    "state": "TX",
                    "zip": "75380",
                },
            ),
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W1430028",
                    "payment_method_id": "credit_card_3414703",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W1430028",
                    "item_ids": ["4107812777", "4965355367"],
                    "new_item_ids": ["4153505238", "4725166838"],
                    "payment_method_id": "paypal_5206520",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W2922433",
                    "item_ids": ["5745575001", "4913411651"],
                    "payment_method_id": "credit_card_3414703",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="isabella_santos_1643",
        instruction="Your name is Isabella Santos and your zip code is 10020. You are impatient, polite. Cancel order #W9667707 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W9667707", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ivan_khan_7475",
        instruction="Your name is Ivan Khan and your email is ivan.khan6479@example.com. You are organized, confident, logical, sad. For #W5270061, change payment to paypal_7729105. For #W5270061, modify Desk Lamp {'color': 'silver', 'brightness': 'low', 'power source': 'battery'} to {'brightness': 'medium', 'power source': 'USB'}; via gift_card_1711656. For #W5782623, change address to {'order_id': '#W5782623', 'address1': '584 Sunset Drive', 'address2': 'Suite 270', 'city': 'Washington', 'country': 'USA', 'state': 'DC', 'zip': '20353'} (same as #W5270061). For #W5782623, change payment to paypal_7729105. For #W5782623, modify Perfume {'scent family': 'woody', 'size': '50ml', 'gender': 'women'} to {'scent family': 'fresh', 'gender': 'men'}; via paypal_7729105. For #W1519594, exchange Electric Kettle {'capacity': '1.5L', 'material': 'glass', 'color': 'white'} to {'capacity': '1L', 'material': 'stainless steel', 'color': 'black'}; Wireless Earbuds {'color': 'blue', 'battery life': '6 hours', 'water resistance': 'IPX4'} to {}; via gift_card_1711656. ",
        actions=[
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W5270061",
                    "payment_method_id": "paypal_7729105",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W5270061",
                    "item_ids": ["7453605304"],
                    "new_item_ids": ["5370728469"],
                    "payment_method_id": "gift_card_1711656",
                },
            ),
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W5782623",
                    "address1": "584 Sunset Drive",
                    "address2": "Suite 270",
                    "city": "Washington",
                    "country": "USA",
                    "state": "DC",
                    "zip": "20353",
                },
            ),
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W5782623",
                    "payment_method_id": "paypal_7729105",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W5782623",
                    "item_ids": ["1002370030"],
                    "new_item_ids": ["9007697085"],
                    "payment_method_id": "paypal_7729105",
                },
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W1519594",
                    "item_ids": ["9472539378", "1646531091"],
                    "new_item_ids": ["7602931732", "1646531091"],
                    "payment_method_id": "gift_card_1711656",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="aarav_davis_4756",
        instruction="Your name is Aarav Davis and your zip code is 76150. You are flexible, sad, patient, optimistic, polite. Cancel order #W7430166 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W7430166", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yara_hernandez_3670",
        instruction="Your name is Yara Hernandez and your email is yara.hernandez7166@example.com. You are relaxing, rigid, happy. For #W2156941, exchange Smart Watch {'color': 'black', 'band material': 'silicone', 'display': 'AMOLED'} to {'color': 'gold', 'band material': 'leather', 'display': 'LCD'}; Action Camera {'resolution': '5K', 'waterproof': 'yes', 'color': 'silver'} to {'waterproof': 'no', 'color': 'black'}; via paypal_5589935. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W2156941",
                    "item_ids": ["4920090458", "1586641416"],
                    "new_item_ids": ["9408160950", "7523669277"],
                    "payment_method_id": "paypal_5589935",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_ahmed_6778",
        instruction="Your name is Olivia Ahmed and your zip code is 94152. You are shy, patient. For #W2609687, change address to {'order_id': '#W2609687', 'address1': '553 Main Street', 'address2': 'Suite 389', 'city': 'San Francisco', 'country': 'USA', 'state': 'CA', 'zip': '94152'} (same as #W1579621). For #W2609687, modify Indoor Security Camera {'resolution': '4K', 'field of view': '110 degrees', 'connectivity': 'Ethernet'} to {'field of view': '130 degrees'}; Electric Kettle {'capacity': '1.5L', 'material': 'plastic', 'color': 'black'} to {}; via gift_card_1044904. Return #W3972714 via credit_card_9698900: Hiking Boots; For #W1579621, exchange Portable Charger {'capacity': '5000mAh', 'output': 'USB-C', 'color': 'white'} to {'capacity': '20000mAh'}; Headphones {'type': 'in-ear', 'connectivity': 'wireless', 'color': 'black'} to {'type': 'on-ear', 'color': 'red'}; via credit_card_9698900. ",
        actions=[
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W2609687",
                    "address1": "553 Main Street",
                    "address2": "Suite 389",
                    "city": "San Francisco",
                    "country": "USA",
                    "state": "CA",
                    "zip": "94152",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W2609687",
                    "item_ids": ["3909704820", "5428723833"],
                    "new_item_ids": ["6901578702", "5428723833"],
                    "payment_method_id": "gift_card_1044904",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W3972714",
                    "item_ids": ["2658930189"],
                    "payment_method_id": "credit_card_9698900",
                },
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W1579621",
                    "item_ids": ["7866854614", "7184044281"],
                    "new_item_ids": ["1178356107", "3104857380"],
                    "payment_method_id": "credit_card_9698900",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="isabella_johnson_6293",
        instruction="Your name is Isabella Johnson and your zip code is 98119. You are impatient, logical, messy, curious, direct. Return #W3431083 via paypal_5071744: Wireless Earbuds; Backpack; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W3431083",
                    "item_ids": ["3694871183", "6309044598"],
                    "payment_method_id": "paypal_5071744",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_khan_7091",
        instruction="Your name is Yusuf Khan and your zip code is 75313. You are dependent, patient. For #W3579467, modify Electric Kettle {'capacity': '1.5L', 'material': 'plastic', 'color': 'black'} to {'color': 'white'}; via paypal_5796936. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W3579467",
                    "item_ids": ["5428723833"],
                    "new_item_ids": ["2698416822"],
                    "payment_method_id": "paypal_5796936",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_smith_5265",
        instruction="Your name is Olivia Smith and your zip code is 80216. You are curious, confident. For #W1974181, modify Wristwatch {'strap material': 'silicone', 'dial color': 'blue'} to {}; via credit_card_7971769. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W1974181",
                    "item_ids": ["8886009523"],
                    "new_item_ids": ["8886009523"],
                    "payment_method_id": "credit_card_7971769",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sophia_garcia_5795",
        instruction="Your name is Sophia Garcia and your zip code is 28212. You are cautious, relaxing. Cancel order #W6447372 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W6447372", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_kim_8860",
        instruction="Your name is Ethan Kim and your zip code is 78286. You are messy, polite, optimistic, patient. For #W8296441, modify Gaming Mouse {'color': 'RGB', 'sensor type': 'optical', 'connectivity': 'wired'} to {'color': 'black'}; via gift_card_5701566. Return #W3942875 via gift_card_5701566: Running Shoes; Jigsaw Puzzle; Water Bottle; ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W8296441",
                    "item_ids": ["5796612084"],
                    "new_item_ids": ["3330317167"],
                    "payment_method_id": "gift_card_5701566",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W3942875",
                    "item_ids": ["1775591963", "9779102705", "2366567022"],
                    "payment_method_id": "gift_card_5701566",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="anya_kovacs_9542",
        instruction="Your name is Anya Kovacs and your zip code is 95132. You are busy, polite, dependent, outgoing, curious. Return #W6821773 via credit_card_4829249: Fleece Jacket; Office Chair; Cycling Helmet; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W6821773",
                    "item_ids": ["8590708195", "2386562819", "6048672633"],
                    "payment_method_id": "credit_card_4829249",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_hernandez_6785",
        instruction="Your name is Yusuf Hernandez and your zip code is 80265. You are rigid, insecure, direct. Cancel order #W2466703 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W2466703", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="james_wilson_1842",
        instruction="Your name is James Wilson and your email is james.wilson1461@example.com. You are curious, flexible, insecure. For #W7826235, exchange Bookshelf {'material': 'glass', 'color': 'white', 'height': '3 ft'} to {'material': 'wood', 'color': 'brown', 'height': '6 ft'}; via credit_card_7871433. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W7826235",
                    "item_ids": ["2989722512"],
                    "new_item_ids": ["7154215719"],
                    "payment_method_id": "credit_card_7871433",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="james_li_5688",
        instruction="Your name is James Li and your zip code is 10083. You are pessimistic, confident, relaxing. Return #W3638028 via gift_card_1725971: Jigsaw Puzzle; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W3638028",
                    "item_ids": ["4572024853"],
                    "payment_method_id": "gift_card_1725971",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sophia_garcia_5025",
        instruction="Your name is Sophia Garcia and your zip code is 20156. You are confident, cautious, rigid. Return #W5777276 via credit_card_4147840: Bookshelf; Notebook; Tablet; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W5777276",
                    "item_ids": ["7154215719", "7579176349", "2106335193"],
                    "payment_method_id": "credit_card_4147840",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sofia_li_9219",
        instruction="Your name is Sofia Li and your zip code is 78260. You are independent, insecure, pessimistic, sad. Return #W3916020 via credit_card_8105988: Jigsaw Puzzle; Bicycle; Return #W5416052 via credit_card_8105988: Pet Bed; Cycling Helmet; Smart Watch; Cancel order #W8855135 because ordered by mistake. ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W3916020",
                    "item_ids": ["4068787148", "7758198585"],
                    "payment_method_id": "credit_card_8105988",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W5416052",
                    "item_ids": ["6942241102", "6401214406", "1631806422"],
                    "payment_method_id": "credit_card_8105988",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W8855135", "reason": "ordered by mistake"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sophia_lee_8294",
        instruction="Your name is Sophia Lee and your email is sophia.lee4144@example.com. You are cautious, logical. Return #W7366745 via gift_card_7803378: Grill; Sunglasses; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W7366745",
                    "item_ids": ["7848293342", "9672174103"],
                    "payment_method_id": "gift_card_7803378",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="noah_martin_5764",
        instruction="Your name is Noah Martin and your zip code is 43090. You are dependent, creative, pessimistic, polite, messy. For #W1971958, exchange Electric Kettle {'capacity': '1.5L', 'material': 'plastic', 'color': 'silver'} to {'color': 'black'}; via paypal_7383471. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W1971958",
                    "item_ids": ["9624127908"],
                    "new_item_ids": ["5428723833"],
                    "payment_method_id": "paypal_7383471",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="evelyn_lopez_5487",
        instruction="Your name is Evelyn Lopez and your zip code is 92195. You are creative, organized. Return #W1355800 via credit_card_3566337: Cycling Helmet; For #W3007862, modify Grill {'type': 'electric', 'size': 'medium', 'features': 'side burner'} to {'size': 'portable'}; Running Shoes {'size': '10', 'color': 'white', 'material': 'leather', 'sole': 'EVA'} to {'size': '9', 'material': 'mesh', 'sole': 'rubber'}; via credit_card_3566337. ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W1355800",
                    "item_ids": ["5537798301"],
                    "payment_method_id": "credit_card_3566337",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W3007862",
                    "item_ids": ["5666020311", "1775591963"],
                    "new_item_ids": ["3876764226", "9635758562"],
                    "payment_method_id": "credit_card_3566337",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="daiki_silva_2903",
        instruction="Your name is Daiki Silva and your email is daiki.silva6295@example.com. You are pessimistic, insecure, creative, dependent, outgoing. For #W8835847, modify Bookshelf {'material': 'glass', 'color': 'white', 'height': '5 ft'} to {'material': 'wood', 'height': '4 ft'}; T-Shirt {'color': 'red', 'size': 'XXL', 'material': 'cotton', 'style': 'crew neck'} to {'color': 'blue', 'size': 'S', 'style': 'v-neck'}; Gaming Mouse {'color': 'white', 'sensor type': 'laser', 'connectivity': 'wireless'} to {'color': 'black'}; via gift_card_2652153. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W8835847",
                    "item_ids": ["8895454203", "9354168549", "7420906769"],
                    "new_item_ids": ["8920458606", "8349118980", "8214883393"],
                    "payment_method_id": "gift_card_2652153",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yara_johansson_9032",
        instruction="Your name is Yara Johansson and your email is yara.johansson5198@example.com. You are shy, creative. Return #W6904184 via credit_card_6699629: Electric Kettle; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W6904184",
                    "item_ids": ["8142779083"],
                    "payment_method_id": "credit_card_6699629",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="emma_santos_9753",
        instruction="Your name is Emma Santos and your email is emma.santos7683@example.com. You are impatient, messy, independent, happy, logical. Cancel order #W2918688 because no longer needed. For #W3113816, exchange Office Chair {'material': 'mesh', 'color': 'red', 'armrest': 'none', 'backrest height': 'standard'} to {'material': 'leather', 'color': 'gray', 'armrest': 'fixed', 'backrest height': 'high-back'}; via gift_card_6023546. For #W1620235, change payment to gift_card_6023546. For #W1620235, modify Luggage Set {'piece count': '3-piece', 'color': 'silver', 'material': 'softshell'} to {'piece count': '4-piece', 'color': 'red', 'material': 'hardshell'}; Electric Kettle {'capacity': '1L', 'material': 'plastic', 'color': 'silver'} to {'material': 'glass', 'color': 'black'}; via gift_card_6023546. Return #W1539823 via gift_card_6023546: Smart Watch; Bluetooth Speaker; For #W9655299, change address to {'order_id': '#W9655299', 'address1': '399 Maple Drive', 'address2': 'Suite 470', 'city': 'Phoenix', 'country': 'USA', 'state': 'AZ', 'zip': '85039'} (same as #W2918688). For #W9655299, modify Sunglasses {'frame color': 'brown', 'lens color': 'brown', 'lens type': 'polarized', 'frame material': 'plastic'} to {'frame color': 'silver', 'lens color': 'blue', 'lens type': 'non-polarized'}; Vacuum Cleaner {'type': 'upright', 'bagged/bagless': 'bagless', 'features': 'cordless'} to {'type': 'robotic'}; via gift_card_6023546. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W2918688", "reason": "no longer needed"},
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W3113816",
                    "item_ids": ["4274709903"],
                    "new_item_ids": ["1071497737"],
                    "payment_method_id": "gift_card_6023546",
                },
            ),
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W1620235",
                    "payment_method_id": "gift_card_6023546",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W1620235",
                    "item_ids": ["6690069155", "9132333852"],
                    "new_item_ids": ["9956648681", "2323972008"],
                    "payment_method_id": "gift_card_6023546",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W1539823",
                    "item_ids": ["2860956907", "7597543861"],
                    "payment_method_id": "gift_card_6023546",
                },
            ),
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W9655299",
                    "address1": "399 Maple Drive",
                    "address2": "Suite 470",
                    "city": "Phoenix",
                    "country": "USA",
                    "state": "AZ",
                    "zip": "85039",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W9655299",
                    "item_ids": ["9672174103", "3019027053"],
                    "new_item_ids": ["4329558751", "4806644905"],
                    "payment_method_id": "gift_card_6023546",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_smith_9087",
        instruction="Your name is Ethan Smith and your zip code is 10280. You are flexible, dependent, sad, patient, insecure. For #W6711349, modify Digital Camera {'resolution': '24MP', 'zoom': '5x', 'storage': 'CF card'} to {'resolution': '30MP', 'zoom': '3x', 'storage': 'SD card'}; Electric Toothbrush {'color': 'white', 'speed settings': 'low', 'battery type': 'rechargeable'} to {'color': 'blue', 'battery type': 'AA batteries'}; via paypal_3296755. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6711349",
                    "item_ids": ["4326528037", "6164262152"],
                    "new_item_ids": ["1804581713", "1583904702"],
                    "payment_method_id": "paypal_3296755",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_kim_8860",
        instruction="Your name is Ethan Kim and your email is ethan.kim3231@example.com. You are direct, patient, independent, logical, curious. For #W3942875, exchange Jigsaw Puzzle {'pieces': '1000', 'theme': 'art', 'difficulty level': 'intermediate'} to {'pieces': '2000', 'theme': 'animals'}; Water Bottle {'capacity': '1000ml', 'material': 'stainless steel', 'color': 'blue'} to {'capacity': '750ml', 'material': 'plastic', 'color': 'black'}; Running Shoes {'size': '10', 'color': 'white', 'material': 'leather', 'sole': 'EVA'} to {}; via gift_card_5701566. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W3942875",
                    "item_ids": ["9779102705", "2366567022", "1775591963"],
                    "new_item_ids": ["5645314103", "7199146548", "1775591963"],
                    "payment_method_id": "gift_card_5701566",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="aarav_santos_4279",
        instruction="Your name is Aarav Santos and your email is aarav.santos2789@example.com. You are flexible, dependent, impatient, pessimistic. For #W8309293, exchange Dumbbell Set {'weight range': '30-50 lbs', 'material': 'rubber', 'set type': 'adjustable'} to {'weight range': '55-75 lbs', 'material': 'urethane'}; via credit_card_3816099. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W8309293",
                    "item_ids": ["3735133539"],
                    "new_item_ids": ["6130713659"],
                    "payment_method_id": "credit_card_3816099",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_kim_8860",
        instruction="Your name is Ethan Kim and your email is ethan.kim3231@example.com. You are curious, impatient. Return #W1763367 via gift_card_5701566: Notebook; Espresso Machine; Laptop; Return #W3942875 via gift_card_5701566: Jigsaw Puzzle; Water Bottle; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W1763367",
                    "item_ids": ["1199058591", "3815173328", "6017636844"],
                    "payment_method_id": "gift_card_5701566",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W3942875",
                    "item_ids": ["9779102705", "2366567022"],
                    "payment_method_id": "gift_card_5701566",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="liam_lopez_7019",
        instruction="Your name is Liam Lopez and your zip code is 75388. You are curious, creative. Cancel order #W7555783 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W7555783", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="fatima_li_5040",
        instruction="Your name is Fatima Li and your zip code is 20287. You are relaxing, rigid, outgoing. Cancel order #W4155745 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W4155745", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sophia_nguyen_7885",
        instruction="Your name is Sophia Nguyen and your zip code is 60647. You are shy, optimistic, organized, logical, flexible. For #W4183735, modify Smartphone {'color': 'rose gold', 'storage': '64GB', 'RAM': '8GB', 'screen size': '5.8-inch'} to {'color': 'black', 'storage': '128GB', 'RAM': '4GB', 'screen size': '6.5-inch'}; via gift_card_2415038. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W4183735",
                    "item_ids": ["5311660992"],
                    "new_item_ids": ["5339029584"],
                    "payment_method_id": "gift_card_2415038",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="chen_taylor_6919",
        instruction="Your name is Chen Taylor and your email is chen.taylor8995@example.com. You are insecure, dependent. Cancel order #W4111999 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W4111999", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="amelia_silva_7726",
        instruction="Your name is Amelia Silva and your zip code is 19117. You are shy, impatient, insecure, optimistic. For #W7342738, modify Wireless Earbuds {'color': 'black', 'battery life': '8 hours', 'water resistance': 'IPX7'} to {'battery life': '4 hours', 'water resistance': 'not resistant'}; via gift_card_3491931. Return #W4597054 via gift_card_3491931: Coffee Maker; Smart Watch; Cancel order #W4836353 because no longer needed. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W7342738",
                    "item_ids": ["2499294441"],
                    "new_item_ids": ["4063058357"],
                    "payment_method_id": "gift_card_3491931",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W4597054",
                    "item_ids": ["9862136885", "4900990404"],
                    "payment_method_id": "gift_card_3491931",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W4836353", "reason": "no longer needed"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sofia_moore_9773",
        instruction="Your name is Sofia Moore and your email is sofia.moore4274@example.com. You are cautious, direct, patient, messy. For #W3338814, exchange E-Reader {'screen size': '7-inch', 'connectivity': 'Wi-Fi + Cellular', 'storage': '32GB'} to {}; via credit_card_1893409. For #W1812830, modify Wall Clock {'diameter': '14 inches', 'color': 'black', 'type': 'analog'} to {'diameter': '12 inches', 'color': 'white'}; via credit_card_1893409. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W3338814",
                    "item_ids": ["4273929280"],
                    "new_item_ids": ["4273929280"],
                    "payment_method_id": "credit_card_1893409",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W1812830",
                    "item_ids": ["7791931443"],
                    "new_item_ids": ["6508153405"],
                    "payment_method_id": "credit_card_1893409",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_lee_5921",
        instruction="Your name is Yusuf Lee and your email is yusuf.lee4349@example.com. You are pessimistic, messy, polite, creative, rigid. For #W3631991, exchange Water Bottle {'capacity': '750ml', 'material': 'stainless steel', 'color': 'blue'} to {'capacity': '1000ml', 'color': 'black'}; via paypal_2785678. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W3631991",
                    "item_ids": ["7843064651"],
                    "new_item_ids": ["7661609223"],
                    "payment_method_id": "paypal_2785678",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="aarav_sanchez_6636",
        instruction="Your name is Aarav Sanchez and your email is aarav.sanchez5467@example.com. You are direct, outgoing, optimistic, flexible. Return #W9552705 via gift_card_8922351: Bookshelf; Portable Charger; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W9552705",
                    "item_ids": ["2244749153", "1178356107"],
                    "payment_method_id": "gift_card_8922351",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="fatima_johnson_7581",
        instruction="Your name is Fatima Johnson and your email is fatima.johnson2300@example.com. You are flexible, optimistic, patient, organized, dependent. For #W9389413, exchange Smart Watch {'color': 'gold', 'band material': 'metal', 'display': 'AMOLED'} to {'color': 'silver', 'band material': 'leather', 'display': 'LCD'}; T-Shirt {'color': 'blue', 'size': 'S', 'material': 'polyester', 'style': 'v-neck'} to {'color': 'black', 'size': 'XL', 'material': 'cotton', 'style': 'crew neck'}; via paypal_5364164. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W9389413",
                    "item_ids": ["2554056026", "5047954489"],
                    "new_item_ids": ["9811090008", "2060066974"],
                    "payment_method_id": "paypal_5364164",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ivan_khan_7475",
        instruction="Your name is Ivan Khan and your zip code is 28243. You are confident, organized, creative, busy. Cancel order #W5782623 because ordered by mistake. For #W5270061, modify Desk Lamp {'color': 'silver', 'brightness': 'low', 'power source': 'battery'} to {'color': 'black', 'brightness': 'medium', 'power source': 'AC adapter'}; via paypal_7729105. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W5782623", "reason": "ordered by mistake"},
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W5270061",
                    "item_ids": ["7453605304"],
                    "new_item_ids": ["5320792178"],
                    "payment_method_id": "paypal_7729105",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="fatima_lee_3440",
        instruction="Your name is Fatima Lee and your email is fatima.lee1693@example.com. You are cautious, logical. Cancel order #W8098147 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W8098147", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sophia_hernandez_2054",
        instruction="Your name is Sophia Hernandez and your zip code is 76197. You are shy, creative, independent, pessimistic. Return #W1748126 via gift_card_1139567: Tea Kettle; Cancel order #W4614740 because no longer needed. ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W1748126",
                    "item_ids": ["8293778132"],
                    "payment_method_id": "gift_card_1139567",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W4614740", "reason": "no longer needed"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="fatima_muller_6713",
        instruction="Your name is Fatima Muller and your zip code is 60644. You are logical, messy, insecure, polite, curious. Cancel order #W6851636 because no longer needed. For #W2435638, exchange Digital Camera {'resolution': '20MP', 'zoom': '10x', 'storage': 'CF card'} to {'resolution': '30MP', 'storage': 'SD card'}; via paypal_5541158. For #W9962383, modify Mechanical Keyboard {'switch type': 'linear', 'backlight': 'none', 'size': '80%'} to {'switch type': 'clicky'}; Tea Kettle {'material': 'stainless steel', 'capacity': '2 liters', 'stovetop compatibility': 'gas'} to {}; via paypal_5541158. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W6851636", "reason": "no longer needed"},
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W2435638",
                    "item_ids": ["7583936705"],
                    "new_item_ids": ["9228757377"],
                    "payment_method_id": "paypal_5541158",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W9962383",
                    "item_ids": ["1421289881", "4238115171"],
                    "new_item_ids": ["9665000388", "4238115171"],
                    "payment_method_id": "paypal_5541158",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="aarav_gonzalez_5113",
        instruction="Your name is Aarav Gonzalez and your zip code is 78268. You are direct, organized, patient. For #W6979932, change payment to gift_card_5979071. For #W6979932, change address to {'order_id': '#W6979932', 'address1': '270 River Road', 'address2': 'Suite 611', 'city': 'San Diego', 'country': 'USA', 'state': 'CA', 'zip': '92194'} (same as #W6797115). For #W6979932, modify Cycling Helmet {'size': 'M', 'color': 'blue', 'ventilation': 'low'} to {'size': 'L', 'color': 'black', 'ventilation': 'high'}; via paypal_6121064. ",
        actions=[
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W6979932",
                    "payment_method_id": "gift_card_5979071",
                },
            ),
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W6979932",
                    "address1": "270 River Road",
                    "address2": "Suite 611",
                    "city": "San Diego",
                    "country": "USA",
                    "state": "CA",
                    "zip": "92194",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6979932",
                    "item_ids": ["3339188619"],
                    "new_item_ids": ["1665571435"],
                    "payment_method_id": "paypal_6121064",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sophia_hernandez_2054",
        instruction="Your name is Sophia Hernandez and your email is sophia.hernandez3499@example.com. You are relaxing, insecure. For #W1748126, exchange Indoor Security Camera {'resolution': '2K', 'field of view': '160 degrees', 'connectivity': 'Ethernet'} to {'resolution': '4K', 'field of view': '130 degrees'}; Tea Kettle {'material': 'ceramic', 'capacity': '1.5 liters', 'stovetop compatibility': 'electric'} to {'material': 'stainless steel', 'capacity': '2 liters', 'stovetop compatibility': 'gas'}; via gift_card_1139567. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W1748126",
                    "item_ids": ["5966895767", "8293778132"],
                    "new_item_ids": ["6901578702", "4238115171"],
                    "payment_method_id": "gift_card_1139567",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_ahmed_6232",
        instruction="Your name is Yusuf Ahmed and your zip code is 91075. You are patient, optimistic, creative. For #W1302858, modify Gaming Mouse {'color': 'RGB', 'sensor type': 'optical', 'connectivity': 'wired'} to {'color': 'white', 'connectivity': 'wireless'}; via credit_card_2167533. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W1302858",
                    "item_ids": ["5796612084"],
                    "new_item_ids": ["8896479688"],
                    "payment_method_id": "credit_card_2167533",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_thomas_1791",
        instruction="Your name is Ethan Thomas and your zip code is 43188. You are insecure, patient, relaxing. Cancel order #W8465042 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W8465042", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ivan_khan_7475",
        instruction="Your name is Ivan Khan and your zip code is 28243. You are pessimistic, sad, flexible, cautious, impatient. For #W1519594, exchange Electric Kettle {'capacity': '1.5L', 'material': 'glass', 'color': 'white'} to {'material': 'plastic'}; via paypal_7729105. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W1519594",
                    "item_ids": ["9472539378"],
                    "new_item_ids": ["2698416822"],
                    "payment_method_id": "paypal_7729105",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_gonzalez_8900",
        instruction="Your name is Yusuf Gonzalez and your email is yusuf.gonzalez2399@example.com. You are polite, rigid, insecure. For #W2806889, modify Tea Kettle {'material': 'ceramic', 'capacity': '1.5 liters', 'stovetop compatibility': 'gas'} to {'material': 'glass', 'capacity': '2 liters', 'stovetop compatibility': 'induction'}; via credit_card_7918119. For #W1679211, exchange T-Shirt {'color': 'blue', 'size': 'M', 'material': 'cotton', 'style': 'crew neck'} to {'size': 'S', 'style': 'v-neck'}; via credit_card_7918119. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W2806889",
                    "item_ids": ["7497340597"],
                    "new_item_ids": ["7292993796"],
                    "payment_method_id": "credit_card_7918119",
                },
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W1679211",
                    "item_ids": ["9612497925"],
                    "new_item_ids": ["8349118980"],
                    "payment_method_id": "credit_card_7918119",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="amelia_rossi_5121",
        instruction="Your name is Amelia Rossi and your email is amelia.rossi1299@example.com. You are flexible, direct. For #W8255453, modify Laptop {'screen size': '17-inch', 'processor': 'i5', 'ram': '8GB', 'storage': '1TB SSD', 'color': 'space grey'} to {'screen size': '13-inch', 'ram': '16GB', 'storage': '512GB SSD'}; T-Shirt {'color': 'blue', 'size': 'M', 'material': 'cotton', 'style': 'crew neck'} to {'color': 'black', 'size': 'XXL', 'material': 'polyester', 'style': 'v-neck'}; via gift_card_5591026. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W8255453",
                    "item_ids": ["3334537816", "9612497925"],
                    "new_item_ids": ["6056040996", "5253880258"],
                    "payment_method_id": "gift_card_5591026",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sophia_hernandez_2054",
        instruction="Your name is Sophia Hernandez and your email is sophia.hernandez3499@example.com. You are optimistic, sad, flexible, curious, relaxing. For #W1748126, exchange Indoor Security Camera {'resolution': '2K', 'field of view': '160 degrees', 'connectivity': 'Ethernet'} to {'field of view': '130 degrees'}; Tea Kettle {'material': 'ceramic', 'capacity': '1.5 liters', 'stovetop compatibility': 'electric'} to {}; via gift_card_1139567. For #W4614740, modify Wristwatch {'strap material': 'metal', 'dial color': 'blue'} to {'strap material': 'silicone', 'dial color': 'white'}; Tablet {'screen size': '8-inch', 'storage': '64GB', 'color': 'silver'} to {'screen size': '7-inch', 'storage': '32GB'}; via gift_card_1139567. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W1748126",
                    "item_ids": ["5966895767", "8293778132"],
                    "new_item_ids": ["8470360507", "8293778132"],
                    "payment_method_id": "gift_card_1139567",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W4614740",
                    "item_ids": ["9112290483", "8551474201"],
                    "new_item_ids": ["2226219750", "4615543240"],
                    "payment_method_id": "gift_card_1139567",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="amelia_patel_7834",
        instruction="Your name is Amelia Patel and your zip code is 85051. You are messy, impatient, relaxing. Cancel order #W9077472 because ordered by mistake. For #W2079779, modify Sunglasses {'frame color': 'black', 'lens color': 'brown', 'lens type': 'polarized', 'frame material': 'plastic'} to {'frame color': 'silver', 'lens color': 'blue', 'lens type': 'non-polarized'}; Action Camera {'resolution': '1080p', 'waterproof': 'no', 'color': 'black'} to {'resolution': '5K'}; via gift_card_3751659. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W9077472", "reason": "ordered by mistake"},
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W2079779",
                    "item_ids": ["4358482460", "9168994198"],
                    "new_item_ids": ["4329558751", "7523669277"],
                    "payment_method_id": "gift_card_3751659",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ivan_johnson_6036",
        instruction="Your name is Ivan Johnson and your email is ivan.johnson5749@example.com. You are rigid, happy, optimistic, insecure. Return #W1671835 via paypal_6918118: Perfume; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W1671835",
                    "item_ids": ["5081446110"],
                    "payment_method_id": "paypal_6918118",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="raj_lopez_5873",
        instruction="Your name is Raj Lopez and your email is raj.lopez2997@example.com. You are confident, flexible. Cancel order #W5107138 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W5107138", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lucas_brown_6720",
        instruction="Your name is Lucas Brown and your email is lucas.brown9344@example.com. You are dependent, pessimistic, patient, outgoing, cautious. For #W8660475, exchange Espresso Machine {'pressure': '15 bar', 'capacity': '1L', 'type': 'manual'} to {'pressure': '19 bar', 'capacity': '2L', 'type': 'capsule'}; via credit_card_2112420. For #W4860251, modify Luggage Set {'piece count': '2-piece', 'color': 'silver', 'material': 'hardshell'} to {'color': 'black', 'material': 'softshell'}; via credit_card_2112420. For #W9218746, exchange Vacuum Cleaner {'type': 'canister', 'bagged/bagless': 'bagged', 'features': 'pet hair removal'} to {'type': 'robotic', 'bagged/bagless': 'bagless', 'features': 'cordless'}; via credit_card_2112420. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W8660475",
                    "item_ids": ["3714494375"],
                    "new_item_ids": ["1157853815"],
                    "payment_method_id": "credit_card_2112420",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W4860251",
                    "item_ids": ["5209958006"],
                    "new_item_ids": ["8926329222"],
                    "payment_method_id": "credit_card_2112420",
                },
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W9218746",
                    "item_ids": ["2872451762"],
                    "new_item_ids": ["4806644905"],
                    "payment_method_id": "credit_card_2112420",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_patel_7767",
        instruction="Your name is Yusuf Patel and your zip code is 94117. You are curious, organized, independent, confident, relaxing. Return #W2274128 via gift_card_3372949: Hiking Boots; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W2274128",
                    "item_ids": ["2185126308"],
                    "payment_method_id": "gift_card_3372949",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_lopez_6291",
        instruction="Your name is Ethan Lopez and your email is ethan.lopez8943@example.com. You are shy, cautious. Return #W8632528 via gift_card_7219486: Backpack; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W8632528",
                    "item_ids": ["5917587651"],
                    "payment_method_id": "gift_card_7219486",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lei_patel_5376",
        instruction="Your name is Lei Patel and your email is lei.patel3765@example.com. You are optimistic, messy, relaxing, creative, shy. For #W4172216, modify Skateboard {'deck material': 'maple', 'length': '34 inch', 'design': 'graphic'} to {'deck material': 'bamboo', 'length': '31 inch', 'design': 'custom'}; Electric Toothbrush {'color': 'black', 'speed settings': 'high', 'battery type': 'AA batteries'} to {'color': 'white', 'speed settings': 'low', 'battery type': 'rechargeable'}; via credit_card_6450011. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W4172216",
                    "item_ids": ["2343503231", "8798690242"],
                    "new_item_ids": ["6313971174", "6164262152"],
                    "payment_method_id": "credit_card_6450011",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="raj_kovacs_9155",
        instruction="Your name is Raj Kovacs and your zip code is 19104. You are happy, logical, independent, outgoing. For #W8455874, exchange E-Reader {'screen size': '7-inch', 'connectivity': 'Wi-Fi + Cellular', 'storage': '32GB'} to {'screen size': '8-inch', 'connectivity': 'Wi-Fi', 'storage': '8GB'}; Skateboard {'deck material': 'bamboo', 'length': '31 inch', 'design': 'custom'} to {'deck material': 'plastic', 'length': '28 inch'}; via gift_card_7032928. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W8455874",
                    "item_ids": ["4273929280", "6313971174"],
                    "new_item_ids": ["9494281769", "2177997696"],
                    "payment_method_id": "gift_card_7032928",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="emma_martin_6993",
        instruction="Your name is Emma Martin and your zip code is 78750. You are organized, insecure, shy, creative. For #W5432440, modify Portable Charger {'capacity': '20000mAh', 'output': 'Wireless', 'color': 'black'} to {'capacity': '10000mAh', 'output': 'USB-C', 'color': 'blue'}; via paypal_6129397. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W5432440",
                    "item_ids": ["8349903180"],
                    "new_item_ids": ["7884173033"],
                    "payment_method_id": "paypal_6129397",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ava_lopez_2676",
        instruction="Your name is Ava Lopez and your email is ava.lopez3569@example.com. You are sad, shy, direct. Cancel order #W5911003 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W5911003", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lucas_johansson_1090",
        instruction="Your name is Lucas Johansson and your zip code is 94147. You are patient, direct, logical, cautious, happy. Cancel order #W5073920 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W5073920", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="liam_gonzalez_4265",
        instruction="Your name is Liam Gonzalez and your email is liam.gonzalez4478@example.com. You are relaxing, happy. Cancel order #W8747662 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W8747662", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="liam_muller_2272",
        instruction="Your name is Liam Muller and your zip code is 60642. You are impatient, curious, outgoing. For #W6818211, exchange Cycling Helmet {'size': 'M', 'color': 'blue', 'ventilation': 'high'} to {}; via paypal_3976765. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W6818211",
                    "item_ids": ["9013366374"],
                    "new_item_ids": ["9013366374"],
                    "payment_method_id": "paypal_3976765",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="omar_moore_9540",
        instruction="Your name is Omar Moore and your zip code is 10096. You are organized, busy, shy, logical. Return #W1874267 via credit_card_8008637: Digital Camera; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W1874267",
                    "item_ids": ["2284404181"],
                    "payment_method_id": "credit_card_8008637",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="liam_thomas_7882",
        instruction="Your name is Liam Thomas and your zip code is 85049. You are shy, logical. Cancel order #W1654931 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W1654931", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mohamed_santos_2427",
        instruction="Your name is Mohamed Santos and your zip code is 76188. You are relaxing, optimistic, confident, organized. For #W4840405, exchange Tablet {'screen size': '8-inch', 'storage': '128GB', 'color': 'black'} to {'screen size': '7-inch'}; via gift_card_4710915. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W4840405",
                    "item_ids": ["7187199153"],
                    "new_item_ids": ["4913411651"],
                    "payment_method_id": "gift_card_4710915",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="liam_thomas_7882",
        instruction="Your name is Liam Thomas and your zip code is 85049. You are outgoing, impatient, logical. Return #W8488728 via paypal_3650980: Hiking Boots; For #W1654931, modify E-Reader {'screen size': '7-inch', 'connectivity': 'Wi-Fi', 'storage': '8GB'} to {'connectivity': 'Wi-Fi + Cellular'}; Air Purifier {'room size': 'small', 'filter type': 'ionic', 'features': 'quiet operation'} to {'room size': 'medium', 'filter type': 'carbon'}; via paypal_3650980. For #W6397299, exchange Vacuum Cleaner {'type': 'canister', 'bagged/bagless': 'bagged', 'features': 'pet hair removal'} to {'type': 'robotic', 'bagged/bagless': 'bagless', 'features': 'HEPA filter'}; Dumbbell Set {'weight range': '5-25 lbs', 'material': 'rubber', 'set type': 'adjustable'} to {'material': 'urethane'}; via credit_card_3261838. ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W8488728",
                    "item_ids": ["5676696062"],
                    "payment_method_id": "paypal_3650980",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W1654931",
                    "item_ids": ["6268080249", "5669664287"],
                    "new_item_ids": ["5418781403", "9375701158"],
                    "payment_method_id": "paypal_3650980",
                },
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W6397299",
                    "item_ids": ["2872451762", "7896397433"],
                    "new_item_ids": ["4725166838", "3275928196"],
                    "payment_method_id": "credit_card_3261838",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sophia_garcia_1101",
        instruction="Your name is Sophia Garcia and your zip code is 78263. You are optimistic, direct, independent, flexible. For #W8727985, exchange Tablet {'screen size': '10-inch', 'storage': '128GB', 'color': 'black'} to {'storage': '64GB', 'color': 'silver'}; via gift_card_9450778. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W8727985",
                    "item_ids": ["3788616824"],
                    "new_item_ids": ["2106335193"],
                    "payment_method_id": "gift_card_9450778",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_moore_6437",
        instruction="Your name is Yusuf Moore and your email is yusuf.moore9422@example.com. You are creative, independent. For #W8295890, exchange E-Reader {'screen size': '7-inch', 'connectivity': 'Wi-Fi + Cellular', 'storage': '32GB'} to {}; via paypal_4755504. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W8295890",
                    "item_ids": ["4273929280"],
                    "new_item_ids": ["4273929280"],
                    "payment_method_id": "paypal_4755504",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_moore_9003",
        instruction="Your name is Ethan Moore and your zip code is 75339. You are direct, independent, outgoing. Return #W6026015 via credit_card_6361025: Dumbbell Set; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W6026015",
                    "item_ids": ["6130713659"],
                    "payment_method_id": "credit_card_6361025",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="liam_li_5260",
        instruction="Your name is Liam Li and your zip code is 94120. You are patient, direct, curious, happy, independent. Cancel order #W9653558 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W9653558", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ava_moore_2033",
        instruction="Your name is Ava Moore and your zip code is 78234. You are dependent, flexible. Return #W8951014 via gift_card_8168843: Backpack {'color': 'navy', 'size': 'small', 'material': 'nylon', 'compartment': 'laptop'}; Digital Camera; Backpack {'color': 'black', 'size': 'small', 'material': 'nylon', 'compartment': 'laptop'}; Bookshelf; Water Bottle; Cancel order #W4135875 because no longer needed. ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W8951014",
                    "item_ids": [
                        "2492465580",
                        "9644439410",
                        "7824298782",
                        "2244749153",
                        "9127591879",
                    ],
                    "payment_method_id": "gift_card_8168843",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W4135875", "reason": "no longer needed"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_johnson_5450",
        instruction="Your name is Ethan Johnson and your zip code is 10021. You are creative, curious. Cancel order #W4250290 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W4250290", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_kim_8860",
        instruction="Your name is Ethan Kim and your email is ethan.kim3231@example.com. You are messy, relaxing, independent. Return #W3942875 via gift_card_5701566: Running Shoes; Water Bottle; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W3942875",
                    "item_ids": ["1775591963", "2366567022"],
                    "payment_method_id": "gift_card_5701566",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ava_silva_4632",
        instruction="Your name is Ava Silva and your email is ava.silva8820@example.com. You are polite, pessimistic, messy, curious. Cancel order #W6805991 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W6805991", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_muller_6097",
        instruction="Your name is Ethan Muller and your zip code is 98128. You are creative, confident, happy, cautious. For #W4398027, exchange Perfume {'scent family': 'oriental', 'size': '30ml', 'gender': 'unisex'} to {'scent family': 'woody', 'size': '100ml', 'gender': 'men'}; Jigsaw Puzzle {'pieces': '1500', 'theme': 'art', 'difficulty level': 'intermediate'} to {}; via credit_card_5721095. Return #W3155037 via credit_card_5721095: Smartphone; Laptop; ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W4398027",
                    "item_ids": ["1725100896", "5546244844"],
                    "new_item_ids": ["3399869890", "5546244844"],
                    "payment_method_id": "credit_card_5721095",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W3155037",
                    "item_ids": ["3952176596", "4241599783"],
                    "payment_method_id": "credit_card_5721095",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="noah_li_2316",
        instruction="Your name is Noah Li and your email is noah.li7327@example.com. You are polite, pessimistic, confident, outgoing, patient. Return #W8553554 via credit_card_4467209: Pet Bed; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W8553554",
                    "item_ids": ["4537595158"],
                    "payment_method_id": "credit_card_4467209",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="liam_thomas_8833",
        instruction="Your name is Liam Thomas and your email is liam.thomas4271@example.com. You are direct, relaxing, pessimistic. For #W3761872, modify Vacuum Cleaner {'type': 'upright', 'bagged/bagless': 'bagless', 'features': 'cordless'} to {'type': 'canister', 'features': 'pet hair removal'}; Espresso Machine {'pressure': '9 bar', 'capacity': '2L', 'type': 'automatic'} to {'capacity': '1L', 'type': 'capsule'}; via credit_card_7287775. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W3761872",
                    "item_ids": ["3019027053", "3709608322"],
                    "new_item_ids": ["7958300294", "7806008610"],
                    "payment_method_id": "credit_card_7287775",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sofia_thomas_1518",
        instruction="Your name is Sofia Thomas and your zip code is 75307. You are curious, shy. For #W2297866, modify Vacuum Cleaner {'type': 'upright', 'bagged/bagless': 'bagless', 'features': 'HEPA filter'} to {'type': 'robotic', 'features': 'pet hair removal'}; via paypal_5334408. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W2297866",
                    "item_ids": ["7407609582"],
                    "new_item_ids": ["4965355367"],
                    "payment_method_id": "paypal_5334408",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="omar_moore_9540",
        instruction="Your name is Omar Moore and your zip code is 10096. You are impatient, independent. Return #W1874267 via credit_card_8008637: Digital Camera; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W1874267",
                    "item_ids": ["2284404181"],
                    "payment_method_id": "credit_card_8008637",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="harper_kovacs_9747",
        instruction="Your name is Harper Kovacs and your email is harper.kovacs6209@example.com. You are pessimistic, curious, organized, impatient. For #W6221400, exchange Air Purifier {'room size': 'medium', 'filter type': 'HEPA', 'features': 'smart sensors'} to {'room size': 'small', 'filter type': 'ionic', 'features': 'quiet operation'}; Water Bottle {'capacity': '750ml', 'material': 'stainless steel', 'color': 'blue'} to {'color': 'red'}; Perfume {'scent family': 'oriental', 'size': '30ml', 'gender': 'unisex'} to {'scent family': 'woody', 'size': '100ml', 'gender': 'men'}; via gift_card_5087631. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W6221400",
                    "item_ids": ["4035304400", "7843064651", "1725100896"],
                    "new_item_ids": ["5669664287", "6777246137", "3399869890"],
                    "payment_method_id": "gift_card_5087631",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="amelia_silva_7726",
        instruction="Your name is Amelia Silva and your email is amelia.silva7872@example.com. You are shy, direct. Return #W7773202 via gift_card_3491931: Hiking Boots; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W7773202",
                    "item_ids": ["8277474082"],
                    "payment_method_id": "gift_card_3491931",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sophia_martin_8570",
        instruction="Your name is Sophia Martin and your zip code is 77034. You are relaxing, happy, insecure, impatient. For #W1603792, change address to {'order_id': '#W1603792', 'address1': '592 Elm Avenue', 'address2': 'Suite 978', 'city': 'Houston', 'country': 'USA', 'state': 'TX', 'zip': '77242'} (same as #W1092119). For #W1603792, modify Bicycle {'frame size': 'large', 'color': 'red', 'type': 'mountain'} to {'frame size': 'medium', 'color': 'black'}; via credit_card_5694100. ",
        actions=[
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W1603792",
                    "address1": "592 Elm Avenue",
                    "address2": "Suite 978",
                    "city": "Houston",
                    "country": "USA",
                    "state": "TX",
                    "zip": "77242",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W1603792",
                    "item_ids": ["5606522780"],
                    "new_item_ids": ["2143041831"],
                    "payment_method_id": "credit_card_5694100",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sophia_hernandez_2054",
        instruction="Your name is Sophia Hernandez and your zip code is 76197. You are busy, direct. Return #W1748126 via gift_card_1139567: Indoor Security Camera; Tea Kettle; For #W1326557, exchange Tablet {'screen size': '7-inch', 'storage': '32GB', 'color': 'gold'} to {}; via gift_card_1139567. ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W1748126",
                    "item_ids": ["5966895767", "8293778132"],
                    "payment_method_id": "gift_card_1139567",
                },
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W1326557",
                    "item_ids": ["6501071631"],
                    "new_item_ids": ["6501071631"],
                    "payment_method_id": "gift_card_1139567",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mei_kovacs_5767",
        instruction="Your name is Mei Kovacs and your email is mei.kovacs4296@example.com. You are rigid, outgoing, cautious, messy, busy. For #W5382576, exchange Smartphone {'color': 'gold', 'storage': '128GB', 'RAM': '4GB', 'screen size': '5.8-inch'} to {'color': 'black', 'screen size': '6.5-inch'}; via gift_card_1776915. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W5382576",
                    "item_ids": ["9929635042"],
                    "new_item_ids": ["5339029584"],
                    "payment_method_id": "gift_card_1776915",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mei_jackson_1214",
        instruction="Your name is Mei Jackson and your email is mei.jackson3801@example.com. You are patient, cautious, polite, sad, busy. For #W5881725, exchange Hiking Boots {'size': '11', 'material': 'leather', 'waterproof': 'yes'} to {}; via paypal_8305620. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W5881725",
                    "item_ids": ["6159919747"],
                    "new_item_ids": ["6159919747"],
                    "payment_method_id": "paypal_8305620",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_jackson_7865",
        instruction="Your name is Yusuf Jackson and your zip code is 98127. You are impatient, independent, busy. Return #W7128968 via paypal_3392566: Vacuum Cleaner; Bluetooth Speaker; Pet Bed; Bookshelf; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W7128968",
                    "item_ids": [
                        "6259501109",
                        "2652637226",
                        "7729002517",
                        "7539442683",
                    ],
                    "payment_method_id": "paypal_3392566",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_davis_3316",
        instruction="Your name is Olivia Davis and your email is olivia.davis4495@example.com. You are sad, independent, busy, polite, patient. Return #W7623533 via paypal_8673863: Jigsaw Puzzle; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W7623533",
                    "item_ids": ["4772738468"],
                    "payment_method_id": "paypal_8673863",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="emma_kovacs_5477",
        instruction="Your name is Emma Kovacs and your zip code is 95111. You are shy, creative. For #W6554908, change address to {'order_id': '#W6554908', 'address1': '111 Sunset Drive', 'address2': 'Suite 183', 'city': 'San Diego', 'country': 'USA', 'state': 'CA', 'zip': '92179'} (same as #W3618959). For #W6554908, modify Skateboard {'deck material': 'maple', 'length': '28 inch', 'design': 'graphic'} to {'deck material': 'plastic', 'design': 'plain'}; Perfume {'scent family': 'fresh', 'size': '30ml', 'gender': 'men'} to {'scent family': 'oriental'}; via gift_card_9246707. For #W7109609, change address to {'order_id': '#W7109609', 'address1': '111 Sunset Drive', 'address2': 'Suite 183', 'city': 'San Diego', 'country': 'USA', 'state': 'CA', 'zip': '92179'} (same as #W3618959). For #W7109609, modify Vacuum Cleaner {'type': 'robotic', 'bagged/bagless': 'bagless', 'features': 'cordless'} to {'features': 'pet hair removal'}; via gift_card_9246707. ",
        actions=[
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W6554908",
                    "address1": "111 Sunset Drive",
                    "address2": "Suite 183",
                    "city": "San Diego",
                    "country": "USA",
                    "state": "CA",
                    "zip": "92179",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6554908",
                    "item_ids": ["2819462352", "9447903288"],
                    "new_item_ids": ["4545791457", "1325156478"],
                    "payment_method_id": "gift_card_9246707",
                },
            ),
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W7109609",
                    "address1": "111 Sunset Drive",
                    "address2": "Suite 183",
                    "city": "San Diego",
                    "country": "USA",
                    "state": "CA",
                    "zip": "92179",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W7109609",
                    "item_ids": ["4806644905"],
                    "new_item_ids": ["4965355367"],
                    "payment_method_id": "gift_card_9246707",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_garcia_3055",
        instruction="Your name is Yusuf Garcia and your email is yusuf.garcia2909@example.com. You are dependent, rigid. For #W3260419, modify Smart Watch {'color': 'black', 'band material': 'silicone', 'display': 'LCD'} to {}; Smart Watch {'color': 'silver', 'band material': 'metal', 'display': 'AMOLED'} to {'color': 'gold', 'band material': 'leather', 'display': 'LCD'}; via paypal_7503218. For #W6885344, modify Backpack {'color': 'grey', 'size': 'medium', 'material': 'polyester', 'compartment': 'laptop'} to {'color': 'black', 'size': 'large'}; via paypal_7503218. For #W2286012, exchange Perfume {'scent family': 'oriental', 'size': '100ml', 'gender': 'men'} to {'scent family': 'woody', 'size': '30ml', 'gender': 'women'}; Bluetooth Speaker {'color': 'black', 'battery life': '20 hours', 'water resistance': 'yes'} to {'color': 'blue'}; via credit_card_8405687. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W3260419",
                    "item_ids": ["2860956907", "4900990404"],
                    "new_item_ids": ["2860956907", "9408160950"],
                    "payment_method_id": "paypal_7503218",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6885344",
                    "item_ids": ["5917587651"],
                    "new_item_ids": ["6906307980"],
                    "payment_method_id": "paypal_7503218",
                },
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W2286012",
                    "item_ids": ["5421902839", "6455132774"],
                    "new_item_ids": ["8316205423", "3254583681"],
                    "payment_method_id": "credit_card_8405687",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_brown_4616",
        instruction="Your name is Olivia Brown and your zip code is 43118. You are relaxing, sad, organized, flexible, curious. Return #W2912153 via credit_card_3081930: Electric Kettle; Desk Lamp; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W2912153",
                    "item_ids": ["9472539378", "1270145486"],
                    "payment_method_id": "credit_card_3081930",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="emma_smith_8564",
        instruction="Your name is Emma Smith and your email is emma.smith3991@example.com. You are curious, happy, organized. Cancel order #W2417020 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W2417020", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mei_martin_6103",
        instruction="Your name is Mei Martin and your zip code is 78270. You are sad, flexible. For #W1759614, exchange Grill {'type': 'electric', 'size': 'large', 'features': 'rotisserie'} to {'type': 'charcoal', 'size': 'medium'}; via credit_card_8398849. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W1759614",
                    "item_ids": ["4404981319"],
                    "new_item_ids": ["7082455361"],
                    "payment_method_id": "credit_card_8398849",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="evelyn_patel_8882",
        instruction="Your name is Evelyn Patel and your email is evelyn.patel2010@example.com. You are independent, cautious, relaxing, happy, messy. For #W6385395, modify T-Shirt {'color': 'purple', 'size': 'XL', 'material': 'cotton', 'style': 'crew neck'} to {'color': 'blue', 'size': 'M'}; Fleece Jacket {'size': 'S', 'color': 'red', 'zipper': 'half'} to {'size': 'L'}; via paypal_3704667. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6385395",
                    "item_ids": ["8124970213", "5992316252"],
                    "new_item_ids": ["9612497925", "8733974883"],
                    "payment_method_id": "paypal_3704667",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mason_wilson_4597",
        instruction="Your name is Mason Wilson and your zip code is 85028. You are confident, optimistic, polite. For #W4318885, modify Bluetooth Speaker {'color': 'blue', 'battery life': '10 hours', 'water resistance': 'yes'} to {'battery life': '20 hours', 'water resistance': 'no'}; via gift_card_6767859. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W4318885",
                    "item_ids": ["4716977452"],
                    "new_item_ids": ["2635605237"],
                    "payment_method_id": "gift_card_6767859",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yara_silva_7567",
        instruction="Your name is Yara Silva and your zip code is 77159. You are dependent, pessimistic. Cancel order #W3730488 because no longer needed. For #W3964602, exchange Bluetooth Speaker {'color': 'green', 'battery life': '10 hours', 'water resistance': 'no'} to {'color': 'red'}; via gift_card_7252880. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W3730488", "reason": "no longer needed"},
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W3964602",
                    "item_ids": ["9179378709"],
                    "new_item_ids": ["1689914594"],
                    "payment_method_id": "gift_card_7252880",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mei_kim_3337",
        instruction="Your name is Mei Kim and your email is mei.kim6594@example.com. You are creative, messy, outgoing, cautious, independent. Cancel order #W3263208 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W3263208", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="omar_santos_4830",
        instruction="Your name is Omar Santos and your email is omar.santos1752@example.com. You are flexible, patient. For #W9121070, change payment to credit_card_8992222. For #W9121070, modify Backpack {'color': 'black', 'size': 'medium', 'material': 'nylon', 'compartment': 'hydration'} to {'color': 'green', 'size': 'small', 'material': 'polyester', 'compartment': 'camera'}; via gift_card_3895897. ",
        actions=[
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W9121070",
                    "payment_method_id": "credit_card_8992222",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W9121070",
                    "item_ids": ["8030558068"],
                    "new_item_ids": ["9851293632"],
                    "payment_method_id": "gift_card_3895897",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="noah_brown_6181",
        instruction="Your name is Noah Brown and your email is noah.brown7922@example.com. You are happy, messy, confident, cautious. Return #W7678072 via paypal_5727330: Gaming Mouse; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W7678072",
                    "item_ids": ["2193628750"],
                    "payment_method_id": "paypal_5727330",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="noah_brown_6181",
        instruction="Your name is Noah Brown and your zip code is 80279. You are impatient, logical, sad, confident. For #W7678072, exchange Gaming Mouse {'color': 'black', 'sensor type': 'laser', 'connectivity': 'wired'} to {'color': 'white', 'sensor type': 'optical', 'connectivity': 'wireless'}; via paypal_5727330. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W7678072",
                    "item_ids": ["2193628750"],
                    "new_item_ids": ["8896479688"],
                    "payment_method_id": "paypal_5727330",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ava_lopez_2676",
        instruction="Your name is Ava Lopez and your email is ava.lopez3569@example.com. You are optimistic, direct. For #W5911003, change payment to gift_card_4855547. For #W5911003, modify Garden Hose {'length': '100ft', 'material': 'rubber', 'color': 'black'} to {'length': '50ft', 'material': 'vinyl'}; Office Chair {'material': 'mesh', 'color': 'red', 'armrest': 'none', 'backrest height': 'standard'} to {'material': 'leather', 'color': 'blue', 'backrest height': 'high-back'}; Hiking Boots {'size': '10', 'material': 'leather', 'waterproof': 'no'} to {'size': '12', 'material': 'synthetic'}; via credit_card_7772870. For #W8327915, change address to {'order_id': '#W8327915', 'address1': '836 Hickory Lane', 'address2': 'Suite 848', 'city': 'San Diego', 'country': 'USA', 'state': 'CA', 'zip': '92168'} (same as #W5911003). For #W8327915, change payment to credit_card_7772870. For #W8327915, modify Sunglasses {'frame color': 'black', 'lens color': 'brown', 'lens type': 'polarized', 'frame material': 'plastic'} to {'frame color': 'brown'}; Skateboard {'deck material': 'bamboo', 'length': '34 inch', 'design': 'custom'} to {'length': '28 inch'}; via gift_card_4855547. ",
        actions=[
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W5911003",
                    "payment_method_id": "gift_card_4855547",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W5911003",
                    "item_ids": ["1518544029", "4274709903", "2185126308"],
                    "new_item_ids": ["5206946487", "8069050545", "4582956489"],
                    "payment_method_id": "credit_card_7772870",
                },
            ),
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W8327915",
                    "address1": "836 Hickory Lane",
                    "address2": "Suite 848",
                    "city": "San Diego",
                    "country": "USA",
                    "state": "CA",
                    "zip": "92168",
                },
            ),
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W8327915",
                    "payment_method_id": "credit_card_7772870",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W8327915",
                    "item_ids": ["4358482460", "6956751343"],
                    "new_item_ids": ["9672174103", "6673921677"],
                    "payment_method_id": "gift_card_4855547",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="aarav_sanchez_6636",
        instruction="Your name is Aarav Sanchez and your zip code is 60653. You are patient, busy, messy. Return #W9552705 via gift_card_8922351: Cycling Helmet; Bookshelf; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W9552705",
                    "item_ids": ["6697922351", "2244749153"],
                    "payment_method_id": "gift_card_8922351",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="raj_lopez_5873",
        instruction="Your name is Raj Lopez and your zip code is 76195. You are flexible, shy. For #W5107138, change payment to paypal_7007375. For #W5107138, modify Grill {'type': 'electric', 'size': 'medium', 'features': 'side burner'} to {'type': 'charcoal', 'features': 'rotisserie'}; via credit_card_6731308. ",
        actions=[
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W5107138",
                    "payment_method_id": "paypal_7007375",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W5107138",
                    "item_ids": ["5666020311"],
                    "new_item_ids": ["7082455361"],
                    "payment_method_id": "credit_card_6731308",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sophia_garcia_5025",
        instruction="Your name is Sophia Garcia and your zip code is 20156. You are messy, curious, relaxing, direct, patient. Return #W5777276 via credit_card_4147840: Tablet; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W5777276",
                    "item_ids": ["2106335193"],
                    "payment_method_id": "credit_card_4147840",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_garcia_3055",
        instruction="Your name is Yusuf Garcia and your email is yusuf.garcia2909@example.com. You are independent, organized, outgoing, sad, insecure. Cancel order #W3260419 because no longer needed. Return #W2286012 via gift_card_7588375: Electric Toothbrush; Action Camera; Perfume; For #W4794911, exchange T-Shirt {'color': 'purple', 'size': 'S', 'material': 'polyester', 'style': 'v-neck'} to {'color': 'blue', 'material': 'cotton'}; via credit_card_8405687. For #W6885344, change address to {'order_id': '#W6885344', 'address1': '690 Broadway', 'address2': 'Suite 737', 'city': 'Indianapolis', 'country': 'USA', 'state': 'IN', 'zip': '46226'} (same as #W2564042). For #W6885344, change payment to gift_card_7588375. For #W6885344, modify Backpack {'color': 'grey', 'size': 'medium', 'material': 'polyester', 'compartment': 'laptop'} to {'color': 'navy', 'size': 'large'}; via paypal_7503218. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W3260419", "reason": "no longer needed"},
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W2286012",
                    "item_ids": ["8098621301", "7523669277", "5421902839"],
                    "payment_method_id": "gift_card_7588375",
                },
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W4794911",
                    "item_ids": ["9647292434"],
                    "new_item_ids": ["8349118980"],
                    "payment_method_id": "credit_card_8405687",
                },
            ),
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W6885344",
                    "address1": "690 Broadway",
                    "address2": "Suite 737",
                    "city": "Indianapolis",
                    "country": "USA",
                    "state": "IN",
                    "zip": "46226",
                },
            ),
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W6885344",
                    "payment_method_id": "gift_card_7588375",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6885344",
                    "item_ids": ["5917587651"],
                    "new_item_ids": ["8084436579"],
                    "payment_method_id": "paypal_7503218",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mia_garcia_4516",
        instruction="Your name is Mia Garcia and your email is mia.garcia2723@example.com. You are impatient, insecure, outgoing. Return #W5490111 via credit_card_3124723: Action Camera; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W5490111",
                    "item_ids": ["6117189161"],
                    "payment_method_id": "credit_card_3124723",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_hernandez_6785",
        instruction="Your name is Yusuf Hernandez and your zip code is 80265. You are confident, cautious. For #W2466703, change address to {'order_id': '#W2466703', 'address1': '580 Broadway', 'address2': 'Suite 162', 'city': 'Denver', 'country': 'USA', 'state': 'CO', 'zip': '80265'} (same as #W2166301). For #W2466703, modify Fleece Jacket {'size': 'L', 'color': 'black', 'zipper': 'full'} to {'size': 'XS', 'color': 'navy'}; Grill {'type': 'charcoal', 'size': 'medium', 'features': 'side burner'} to {'features': 'rotisserie'}; via paypal_7529813. For #W7739115, exchange Makeup Kit {'skin tone': 'dark', 'kit size': 'professional', 'brand': 'Brand A'} to {'brand': 'Brand C'}; via paypal_7529813. ",
        actions=[
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W2466703",
                    "address1": "580 Broadway",
                    "address2": "Suite 162",
                    "city": "Denver",
                    "country": "USA",
                    "state": "CO",
                    "zip": "80265",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W2466703",
                    "item_ids": ["9385662952", "7848293342"],
                    "new_item_ids": ["8161321868", "7082455361"],
                    "payment_method_id": "paypal_7529813",
                },
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W7739115",
                    "item_ids": ["1573035764"],
                    "new_item_ids": ["1763705424"],
                    "payment_method_id": "paypal_7529813",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lei_ahmed_1705",
        instruction="Your name is Lei Ahmed and your email is lei.ahmed1696@example.com. You are dependent, messy, direct. For #W6724985, modify Bookshelf {'material': 'glass', 'color': 'white', 'height': '5 ft'} to {'color': 'brown'}; via credit_card_3593714. Cancel order #W9132840 because no longer needed. Cancel order #W9015076 because no longer needed. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6724985",
                    "item_ids": ["8895454203"],
                    "new_item_ids": ["4894369688"],
                    "payment_method_id": "credit_card_3593714",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W9132840", "reason": "no longer needed"},
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W9015076", "reason": "no longer needed"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_thomas_1791",
        instruction="Your name is Ethan Thomas and your zip code is 43188. You are confident, polite, busy, curious. Return #W7764382 via gift_card_2519457: Indoor Security Camera; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W7764382",
                    "item_ids": ["3909704820"],
                    "payment_method_id": "gift_card_2519457",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="harper_kim_2998",
        instruction="Your name is Harper Kim and your zip code is 78222. You are polite, creative, messy, confident. For #W7807988, modify Digital Camera {'resolution': '24MP', 'zoom': '3x', 'storage': 'SD card'} to {'resolution': '30MP'}; via gift_card_5328393. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W7807988",
                    "item_ids": ["5996159312"],
                    "new_item_ids": ["1804581713"],
                    "payment_method_id": "gift_card_5328393",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_santos_6104",
        instruction="Your name is Ethan Santos and your zip code is 80278. You are insecure, happy. For #W5320242, modify Cycling Helmet {'size': 'L', 'color': 'blue', 'ventilation': 'high'} to {'size': 'S', 'color': 'white', 'ventilation': 'medium'}; Tablet {'screen size': '7-inch', 'storage': '128GB', 'color': 'black'} to {'screen size': '10-inch', 'storage': '64GB', 'color': 'silver'}; via credit_card_9784468. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W5320242",
                    "item_ids": ["2206116040", "4913411651"],
                    "new_item_ids": ["7811981098", "2106335193"],
                    "payment_method_id": "credit_card_9784468",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="james_martin_1500",
        instruction="Your name is James Martin and your email is james.martin9857@example.com. You are rigid, polite. Cancel order #W3529525 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W3529525", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="amelia_ito_8772",
        instruction="Your name is Amelia Ito and your email is amelia.ito8974@example.com. You are polite, logical, sad, impatient, busy. For #W3883329, modify Cycling Helmet {'size': 'S', 'color': 'black', 'ventilation': 'medium'} to {'color': 'red', 'ventilation': 'low'}; Digital Camera {'resolution': '30MP', 'zoom': '3x', 'storage': 'CF card'} to {'resolution': '24MP', 'storage': 'SD card'}; via paypal_2767694. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W3883329",
                    "item_ids": ["5537798301", "7255224608"],
                    "new_item_ids": ["3358616356", "5996159312"],
                    "payment_method_id": "paypal_2767694",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="liam_li_5260",
        instruction="Your name is Liam Li and your email is liam.li2557@example.com. You are organized, happy. Cancel order #W9653558 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W9653558", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_kim_8860",
        instruction="Your name is Ethan Kim and your email is ethan.kim3231@example.com. You are pessimistic, independent, happy. For #W8296441, modify Action Camera {'resolution': '4K', 'waterproof': 'yes', 'color': 'silver'} to {'resolution': '5K', 'waterproof': 'no', 'color': 'black'}; via gift_card_5701566. Return #W1763367 via gift_card_5701566: Espresso Machine; Notebook; ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W8296441",
                    "item_ids": ["6117189161"],
                    "new_item_ids": ["7523669277"],
                    "payment_method_id": "gift_card_5701566",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W1763367",
                    "item_ids": ["3815173328", "1199058591"],
                    "payment_method_id": "gift_card_5701566",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="emma_kim_1076",
        instruction="Your name is Emma Kim and your zip code is 46214. You are cautious, insecure, creative, direct, flexible. Cancel order #W3698202 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W3698202", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="noah_kovacs_1216",
        instruction="Your name is Noah Kovacs and your email is noah.kovacs8240@example.com. You are patient, shy. Cancel order #W9440076 because no longer needed. For #W3002300, exchange Bluetooth Speaker {'color': 'green', 'battery life': '10 hours', 'water resistance': 'no'} to {'color': 'red', 'battery life': '20 hours', 'water resistance': 'yes'}; Bluetooth Speaker {'color': 'black', 'battery life': '10 hours', 'water resistance': 'no'} to {'color': 'blue', 'battery life': '20 hours'}; via gift_card_2486551. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W9440076", "reason": "no longer needed"},
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W3002300",
                    "item_ids": ["9179378709", "7597543861"],
                    "new_item_ids": ["7617930199", "2635605237"],
                    "payment_method_id": "gift_card_2486551",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yara_moore_6466",
        instruction="Your name is Yara Moore and your email is yara.moore6859@example.com. You are busy, organized, cautious, confident, outgoing. For #W8336711, exchange Smartphone {'color': 'black', 'storage': '128GB', 'RAM': '8GB', 'screen size': '5.8-inch'} to {}; Bluetooth Speaker {'color': 'blue', 'battery life': '10 hours', 'water resistance': 'no'} to {}; Perfume {'scent family': 'woody', 'size': '100ml', 'gender': 'men'} to {'scent family': 'oriental', 'size': '30ml'}; via credit_card_7161839. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W8336711",
                    "item_ids": ["1507389580", "6704763132", "3399869890"],
                    "new_item_ids": ["1507389580", "6704763132", "1325156478"],
                    "payment_method_id": "credit_card_7161839",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ava_nguyen_6646",
        instruction="Your name is Ava Nguyen and your email is ava.nguyen2868@example.com. You are organized, curious, shy, busy, pessimistic. Cancel order #W9892465 because no longer needed. For #W8367380, modify Bluetooth Speaker {'color': 'red', 'battery life': '10 hours', 'water resistance': 'no'} to {'color': 'blue'}; via gift_card_1994993. Cancel order #W9232383 because ordered by mistake. Cancel order #W6272294 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W9892465", "reason": "no longer needed"},
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W8367380",
                    "item_ids": ["1689914594"],
                    "new_item_ids": ["6704763132"],
                    "payment_method_id": "gift_card_1994993",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W9232383", "reason": "ordered by mistake"},
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W6272294", "reason": "no longer needed"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="harper_johansson_2663",
        instruction="Your name is Harper Johansson and your email is harper.johansson4006@example.com. You are independent, organized, rigid. Cancel order #W2912646 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W2912646", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_hernandez_6467",
        instruction="Your name is Yusuf Hernandez and your email is yusuf.hernandez6086@example.com. You are creative, dependent, patient, confident. Return #W7133840 via paypal_9426036: Bookshelf; Backpack; Jigsaw Puzzle; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W7133840",
                    "item_ids": ["6735339143", "4947717507", "7127170374"],
                    "payment_method_id": "paypal_9426036",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yara_sanchez_9145",
        instruction="Your name is Yara Sanchez and your email is yara.sanchez9547@example.com. You are insecure, sad, logical, independent, pessimistic. For #W6519831, exchange Smart Thermostat {'compatibility': 'Apple HomeKit', 'color': 'stainless steel'} to {'compatibility': 'Amazon Alexa'}; via credit_card_5353742. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W6519831",
                    "item_ids": ["9480266227"],
                    "new_item_ids": ["6243148452"],
                    "payment_method_id": "credit_card_5353742",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="fatima_muller_6713",
        instruction="Your name is Fatima Muller and your email is fatima.muller6448@example.com. You are rigid, impatient, curious, pessimistic, dependent. Cancel order #W4160705 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W4160705", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="fatima_brown_2588",
        instruction="Your name is Fatima Brown and your email is fatima.brown8196@example.com. You are flexible, direct, cautious. For #W8008214, modify Espresso Machine {'pressure': '9 bar', 'capacity': '1L', 'type': 'capsule'} to {'pressure': '19 bar', 'capacity': '1.5L', 'type': 'automatic'}; via paypal_8445813. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W8008214",
                    "item_ids": ["7806008610"],
                    "new_item_ids": ["3951031513"],
                    "payment_method_id": "paypal_8445813",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sofia_li_9219",
        instruction="Your name is Sofia Li and your zip code is 78260. You are insecure, independent, organized, optimistic. For #W3916020, exchange Bicycle {'frame size': 'medium', 'color': 'green', 'type': 'road'} to {}; Jigsaw Puzzle {'pieces': '500', 'theme': 'art', 'difficulty level': 'intermediate'} to {'theme': 'animals', 'difficulty level': 'expert'}; via paypal_8194385. For #W8855135, change address to {'order_id': '#W8855135', 'address1': '285 Elm Street', 'address2': 'Suite 121', 'city': 'Fort Worth', 'country': 'USA', 'state': 'TX', 'zip': '76155'} (same as #W3916020). For #W8855135, modify Hiking Boots {'size': '7', 'material': 'synthetic', 'waterproof': 'no'} to {'size': '8'}; via credit_card_8105988. For #W5416052, exchange Pet Bed {'size': 'large', 'material': 'memory foam', 'color': 'beige'} to {'size': 'medium', 'material': 'polyester'}; via credit_card_8105988. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W3916020",
                    "item_ids": ["7758198585", "4068787148"],
                    "new_item_ids": ["7758198585", "9237024510"],
                    "payment_method_id": "paypal_8194385",
                },
            ),
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W8855135",
                    "address1": "285 Elm Street",
                    "address2": "Suite 121",
                    "city": "Fort Worth",
                    "country": "USA",
                    "state": "TX",
                    "zip": "76155",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W8855135",
                    "item_ids": ["1437889264"],
                    "new_item_ids": ["3613716226"],
                    "payment_method_id": "credit_card_8105988",
                },
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W5416052",
                    "item_ids": ["6942241102"],
                    "new_item_ids": ["6499892866"],
                    "payment_method_id": "credit_card_8105988",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_rossi_9620",
        instruction="Your name is Yusuf Rossi and your email is yusuf.rossi7301@example.com. You are patient, happy. Return #W6679257 via credit_card_9513926: Digital Camera; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W6679257",
                    "item_ids": ["5996159312"],
                    "payment_method_id": "credit_card_9513926",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_jackson_7865",
        instruction="Your name is Yusuf Jackson and your email is yusuf.jackson4654@example.com. You are curious, impatient. For #W7128968, exchange Vacuum Cleaner {'type': 'robotic', 'bagged/bagless': 'bagged', 'features': 'pet hair removal'} to {'bagged/bagless': 'bagless', 'features': 'cordless'}; Bluetooth Speaker {'color': 'green', 'battery life': '20 hours', 'water resistance': 'yes'} to {'color': 'blue', 'battery life': '10 hours', 'water resistance': 'no'}; via gift_card_7037673. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W7128968",
                    "item_ids": ["6259501109", "2652637226"],
                    "new_item_ids": ["4806644905", "6704763132"],
                    "payment_method_id": "gift_card_7037673",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_santos_6104",
        instruction="Your name is Ethan Santos and your email is ethan.santos9082@example.com. You are outgoing, pessimistic, independent. For #W5320242, change address to {'order_id': '#W5320242', 'address1': '654 Spruce Street', 'address2': 'Suite 503', 'city': 'Denver', 'country': 'USA', 'state': 'CO', 'zip': '80278'} (same as #W4642822). For #W5320242, modify Indoor Security Camera {'resolution': '2K', 'field of view': '160 degrees', 'connectivity': 'Ethernet'} to {'resolution': '4K', 'field of view': '130 degrees'}; Luggage Set {'piece count': '2-piece', 'color': 'red', 'material': 'softshell'} to {'piece count': '4-piece', 'material': 'hardshell'}; via credit_card_9784468. ",
        actions=[
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W5320242",
                    "address1": "654 Spruce Street",
                    "address2": "Suite 503",
                    "city": "Denver",
                    "country": "USA",
                    "state": "CO",
                    "zip": "80278",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W5320242",
                    "item_ids": ["5966895767", "7160999700"],
                    "new_item_ids": ["6901578702", "9956648681"],
                    "payment_method_id": "credit_card_9784468",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="chen_ahmed_3232",
        instruction="Your name is Chen Ahmed and your zip code is 46210. You are independent, flexible, curious, impatient, direct. For #W8268544, modify Cycling Helmet {'size': 'L', 'color': 'red', 'ventilation': 'high'} to {'size': 'S', 'color': 'white', 'ventilation': 'low'}; Smartphone {'color': 'gold', 'storage': '128GB', 'RAM': '6GB', 'screen size': '6.1-inch'} to {'color': 'black', 'RAM': '8GB', 'screen size': '5.8-inch'}; via gift_card_1402922. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W8268544",
                    "item_ids": ["7401244629", "1631373418"],
                    "new_item_ids": ["1596993217", "1507389580"],
                    "payment_method_id": "gift_card_1402922",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="daiki_li_8218",
        instruction="Your name is Daiki Li and your zip code is 75201. You are insecure, direct. Cancel order #W6958840 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W6958840", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="anya_garcia_3271",
        instruction="Your name is Anya Garcia and your email is anya.garcia2061@example.com. You are dependent, insecure, curious, pessimistic, sad. Cancel order #W6436609 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W6436609", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_johnson_7053",
        instruction="Your name is Ethan Johnson and your email is ethan.johnson2557@example.com. You are impatient, direct, rigid, pessimistic, outgoing. Return #W7450915 via gift_card_6892585: Laptop; Bookshelf; Digital Camera; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W7450915",
                    "item_ids": ["3334537816", "6735339143", "7195021808"],
                    "payment_method_id": "gift_card_6892585",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="chen_silva_7485",
        instruction="Your name is Chen Silva and your email is chen.silva2698@example.com. You are organized, busy. For #W2598834, exchange Jigsaw Puzzle {'pieces': '1500', 'theme': 'animals', 'difficulty level': 'intermediate'} to {'difficulty level': 'beginner'}; via gift_card_7250692. Return #W8171054 via gift_card_7250692: Tea Kettle; Running Shoes; ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W2598834",
                    "item_ids": ["6245746168"],
                    "new_item_ids": ["9665100170"],
                    "payment_method_id": "gift_card_7250692",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W8171054",
                    "item_ids": ["9747045638", "9791469541"],
                    "payment_method_id": "gift_card_7250692",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mia_garcia_4516",
        instruction="Your name is Mia Garcia and your email is mia.garcia2723@example.com. You are pessimistic, outgoing, creative, confident. For #W7387996, exchange Gaming Mouse {'color': 'RGB', 'sensor type': 'optical', 'connectivity': 'wired'} to {'color': 'white'}; via credit_card_3124723. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W7387996",
                    "item_ids": ["5796612084"],
                    "new_item_ids": ["2880340443"],
                    "payment_method_id": "credit_card_3124723",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lei_li_6575",
        instruction="Your name is Lei Li and your email is lei.li8350@example.com. You are shy, logical, rigid, organized. Cancel order #W3414433 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W3414433", "reason": "ordered by mistake"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_jackson_1219",
        instruction="Your name is Olivia Jackson and your zip code is 95119. You are outgoing, polite, busy, organized. Cancel order #W6975922 because no longer needed. Cancel order #W5663445 because ordered by mistake. For #W2090453, modify Espresso Machine {'pressure': '19 bar', 'capacity': '2L', 'type': 'capsule'} to {'pressure': '9 bar', 'type': 'manual'}; Bookshelf {'material': 'glass', 'color': 'white', 'height': '3 ft'} to {'material': 'metal', 'color': 'brown', 'height': '6 ft'}; via paypal_3999493. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W6975922", "reason": "no longer needed"},
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W5663445", "reason": "ordered by mistake"},
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W2090453",
                    "item_ids": ["1157853815", "2989722512"],
                    "new_item_ids": ["7774234341", "6735339143"],
                    "payment_method_id": "paypal_3999493",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="anya_patel_3710",
        instruction="Your name is Anya Patel and your email is anya.patel9309@example.com. You are rigid, organized. For #W4604258, change payment to credit_card_4142574. For #W4604258, modify Bluetooth Speaker {'color': 'black', 'battery life': '10 hours', 'water resistance': 'yes'} to {'color': 'red', 'battery life': '20 hours', 'water resistance': 'no'}; Tea Kettle {'material': 'ceramic', 'capacity': '1.5 liters', 'stovetop compatibility': 'gas'} to {'material': 'glass', 'capacity': '1 liter', 'stovetop compatibility': 'electric'}; Hiking Boots {'size': '8', 'material': 'leather', 'waterproof': 'yes'} to {'size': '11', 'waterproof': 'no'}; via credit_card_4142574. ",
        actions=[
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W4604258",
                    "payment_method_id": "credit_card_4142574",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W4604258",
                    "item_ids": ["5855700373", "7497340597", "2648909398"],
                    "new_item_ids": ["1052700637", "9747045638", "5676696062"],
                    "payment_method_id": "credit_card_4142574",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="evelyn_kovacs_6742",
        instruction="Your name is Evelyn Kovacs and your zip code is 32117. You are optimistic, cautious, dependent, direct. For #W6689278, change address to {'order_id': '#W6689278', 'address1': '505 Cedar Avenue', 'address2': 'Suite 539', 'city': 'Jacksonville', 'country': 'USA', 'state': 'FL', 'zip': '32117'} (same as #W5694685). For #W6689278, modify Electric Kettle {'capacity': '1L', 'material': 'plastic', 'color': 'white'} to {'capacity': '1.5L', 'color': 'silver'}; via paypal_7732922. For #W7398274, change address to {'order_id': '#W7398274', 'address1': '295 Elm Avenue', 'address2': 'Suite 793', 'city': 'Los Angeles', 'country': 'USA', 'state': 'CA', 'zip': '90320'} (same as #W2768683). For #W7398274, modify Notebook {'size': 'A4', 'cover type': 'hard cover'} to {}; Wristwatch {'strap material': 'leather', 'dial color': 'white'} to {'strap material': 'metal', 'dial color': 'black'}; via paypal_7732922. ",
        actions=[
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W6689278",
                    "address1": "505 Cedar Avenue",
                    "address2": "Suite 539",
                    "city": "Jacksonville",
                    "country": "USA",
                    "state": "FL",
                    "zip": "32117",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6689278",
                    "item_ids": ["2243454707"],
                    "new_item_ids": ["9624127908"],
                    "payment_method_id": "paypal_7732922",
                },
            ),
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W7398274",
                    "address1": "295 Elm Avenue",
                    "address2": "Suite 793",
                    "city": "Los Angeles",
                    "country": "USA",
                    "state": "CA",
                    "zip": "90320",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W7398274",
                    "item_ids": ["1199058591", "1355937109"],
                    "new_item_ids": ["1199058591", "4510078629"],
                    "payment_method_id": "paypal_7732922",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lei_wilson_4541",
        instruction="Your name is Lei Wilson and your email is lei.wilson1253@example.com. You are patient, rigid, happy, outgoing, curious. Cancel order #W3826449 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W3826449", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="juan_lopez_5820",
        instruction="Your name is Juan Lopez and your zip code is 85060. You are patient, dependent, shy, rigid, busy. For #W3386832, modify Espresso Machine {'pressure': '9 bar', 'capacity': '2L', 'type': 'automatic'} to {'type': 'manual'}; Cycling Helmet {'size': 'M', 'color': 'blue', 'ventilation': 'low'} to {'color': 'red', 'ventilation': 'medium'}; via paypal_6729210. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W3386832",
                    "item_ids": ["3709608322", "3339188619"],
                    "new_item_ids": ["7774234341", "1719127154"],
                    "payment_method_id": "paypal_6729210",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="evelyn_ahmed_3960",
        instruction="Your name is Evelyn Ahmed and your zip code is 80256. You are messy, creative, direct, outgoing, sad. For #W3746173, change payment to credit_card_7898168. For #W3746173, modify Makeup Kit {'skin tone': 'medium', 'kit size': 'professional', 'brand': 'Brand A'} to {'skin tone': 'dark', 'brand': 'Brand C'}; via gift_card_5683713. ",
        actions=[
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W3746173",
                    "payment_method_id": "credit_card_7898168",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W3746173",
                    "item_ids": ["2882812427"],
                    "new_item_ids": ["1763705424"],
                    "payment_method_id": "gift_card_5683713",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_sanchez_2952",
        instruction="Your name is Ethan Sanchez and your email is ethan.sanchez6360@example.com. You are cautious, insecure. Return #W9250394 via gift_card_4817478: Wristwatch; Dumbbell Set; Smart Watch; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W9250394",
                    "item_ids": ["2407258246", "7159180318", "2681513500"],
                    "payment_method_id": "gift_card_4817478",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="daiki_li_8218",
        instruction="Your name is Daiki Li and your zip code is 75201. You are creative, impatient, curious. For #W6958840, change payment to gift_card_5730441. For #W6958840, modify Cycling Helmet {'size': 'L', 'color': 'black', 'ventilation': 'low'} to {'size': 'S', 'ventilation': 'medium'}; via credit_card_1687024. ",
        actions=[
            Action(
                name="modify_pending_order_payment",
                kwargs={
                    "order_id": "#W6958840",
                    "payment_method_id": "gift_card_5730441",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W6958840",
                    "item_ids": ["6048672633"],
                    "new_item_ids": ["5537798301"],
                    "payment_method_id": "credit_card_1687024",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_patel_7767",
        instruction="Your name is Yusuf Patel and your email is yusuf.patel5348@example.com. You are happy, cautious. For #W1052399, exchange Makeup Kit {'skin tone': 'light', 'kit size': 'basic', 'brand': 'Brand B'} to {'skin tone': 'dark'}; via gift_card_3372949. Cancel order #W2236333 because no longer needed. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W1052399",
                    "item_ids": ["8090061879"],
                    "new_item_ids": ["6254646215"],
                    "payment_method_id": "gift_card_3372949",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W2236333", "reason": "no longer needed"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="daiki_kim_2165",
        instruction="Your name is Daiki Kim and your email is daiki.kim7376@example.com. You are relaxing, logical, shy. Return #W4824466 via gift_card_9919420: Headphones; Hiking Boots; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W4824466",
                    "item_ids": ["5635439102", "8106223139"],
                    "payment_method_id": "gift_card_9919420",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="james_lee_5010",
        instruction="Your name is James Lee and your zip code is 95161. You are messy, confident, direct, shy, busy. For #W5356919, change address to {'order_id': '#W5356919', 'address1': '870 Oak Street', 'address2': 'Suite 766', 'city': 'San Jose', 'country': 'USA', 'state': 'CA', 'zip': '95161'} (same as #W8520591). For #W5356919, modify Jigsaw Puzzle {'pieces': '1000', 'theme': 'art', 'difficulty level': 'expert'} to {'pieces': '500', 'difficulty level': 'intermediate'}; via paypal_2684483. ",
        actions=[
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W5356919",
                    "address1": "870 Oak Street",
                    "address2": "Suite 766",
                    "city": "San Jose",
                    "country": "USA",
                    "state": "CA",
                    "zip": "95161",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W5356919",
                    "item_ids": ["9370300555"],
                    "new_item_ids": ["4068787148"],
                    "payment_method_id": "paypal_2684483",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="noah_patel_6952",
        instruction="Your name is Noah Patel and your zip code is 10108. You are polite, messy. For #W1845024, modify Office Chair {'material': 'fabric', 'color': 'blue', 'armrest': 'adjustable', 'backrest height': 'standard'} to {}; via paypal_3169710. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W1845024",
                    "item_ids": ["8323284863"],
                    "new_item_ids": ["8323284863"],
                    "payment_method_id": "paypal_3169710",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lei_li_6575",
        instruction="Your name is Lei Li and your email is lei.li8350@example.com. You are independent, messy. For #W5166363, change address to {'order_id': '#W5166363', 'address1': '604 Pine Lane', 'address2': 'Suite 907', 'city': 'Phoenix', 'country': 'USA', 'state': 'AZ', 'zip': '85033'} (same as #W3414433). For #W5166363, modify Laptop {'screen size': '17-inch', 'processor': 'i5', 'ram': '8GB', 'storage': '1TB SSD', 'color': 'space grey'} to {'screen size': '15-inch', 'processor': 'i7', 'color': 'black'}; via credit_card_4466831. For #W6289770, exchange Grill {'type': 'electric', 'size': 'portable', 'features': 'none'} to {'type': 'charcoal', 'size': 'medium', 'features': 'side burner'}; Sunglasses {'frame color': 'black', 'lens color': 'green', 'lens type': 'polarized', 'frame material': 'plastic'} to {'lens type': 'non-polarized', 'frame material': 'metal'}; via credit_card_4466831. ",
        actions=[
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W5166363",
                    "address1": "604 Pine Lane",
                    "address2": "Suite 907",
                    "city": "Phoenix",
                    "country": "USA",
                    "state": "AZ",
                    "zip": "85033",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W5166363",
                    "item_ids": ["3334537816"],
                    "new_item_ids": ["9844888101"],
                    "payment_method_id": "credit_card_4466831",
                },
            ),
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W6289770",
                    "item_ids": ["1120917161", "4548300368"],
                    "new_item_ids": ["7848293342", "4245201809"],
                    "payment_method_id": "credit_card_4466831",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mia_smith_1623",
        instruction="Your name is Mia Smith and your email is mia.smith4644@example.com. You are outgoing, dependent, rigid, happy, patient. Return #W5254379 via paypal_3839332: Air Purifier; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W5254379",
                    "item_ids": ["4035304400"],
                    "payment_method_id": "paypal_3839332",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="aarav_davis_4756",
        instruction="Your name is Aarav Davis and your email is aarav.davis1165@example.com. You are optimistic, flexible, relaxing, logical. Cancel order #W3196599 because no longer needed. Cancel order #W2403075 because ordered by mistake. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W3196599", "reason": "no longer needed"},
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W2403075", "reason": "ordered by mistake"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="chen_anderson_8078",
        instruction="Your name is Chen Anderson and your email is chen.anderson4495@example.com. You are insecure, patient. Return #W1701126 via credit_card_9389219: Water Bottle; Makeup Kit; Return #W5332101 via gift_card_3434432: T-Shirt; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W1701126",
                    "item_ids": ["7918497119", "7902309762"],
                    "payment_method_id": "credit_card_9389219",
                },
            ),
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W5332101",
                    "item_ids": ["1176194968"],
                    "payment_method_id": "gift_card_3434432",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lucas_brown_6720",
        instruction="Your name is Lucas Brown and your email is lucas.brown9344@example.com. You are happy, optimistic, outgoing, relaxing. Return #W9218746 via credit_card_2112420: Vacuum Cleaner; Backpack; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W9218746",
                    "item_ids": ["2872451762", "7824298782"],
                    "payment_method_id": "credit_card_2112420",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="raj_santos_9079",
        instruction="Your name is Raj Santos and your zip code is 98157. You are rigid, busy. Return #W1630030 via paypal_2417743: Electric Kettle; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W1630030",
                    "item_ids": ["4458619711"],
                    "payment_method_id": "paypal_2417743",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="daiki_silva_5033",
        instruction="Your name is Daiki Silva and your email is daiki.silva2239@example.com. You are relaxing, sad, pessimistic. Cancel order #W1579160 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W1579160", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="olivia_sanchez_2914",
        instruction="Your name is Olivia Sanchez and your email is olivia.sanchez1894@example.com. You are flexible, logical, sad. For #W5101035, modify Electric Toothbrush {'color': 'black', 'speed settings': 'high', 'battery type': 'AA batteries'} to {'battery type': 'rechargeable'}; via paypal_3388537. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W5101035",
                    "item_ids": ["8798690242"],
                    "new_item_ids": ["8098621301"],
                    "payment_method_id": "paypal_3388537",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lucas_muller_4380",
        instruction="Your name is Lucas Muller and your zip code is 78763. You are patient, direct, relaxing, flexible, pessimistic. For #W3206099, modify Dumbbell Set {'weight range': '30-50 lbs', 'material': 'iron', 'set type': 'fixed'} to {'weight range': '5-25 lbs', 'material': 'urethane'}; via gift_card_2748512. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W3206099",
                    "item_ids": ["3333391894"],
                    "new_item_ids": ["6585768447"],
                    "payment_method_id": "gift_card_2748512",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="noah_hernandez_4232",
        instruction="Your name is Noah Hernandez and your email is noah.hernandez4161@example.com. You are insecure, pessimistic, relaxing, patient. For #W3897284, modify E-Reader {'screen size': '7-inch', 'connectivity': 'Wi-Fi + Cellular', 'storage': '8GB'} to {'storage': '32GB'}; via gift_card_3410768. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W3897284",
                    "item_ids": ["5418781403"],
                    "new_item_ids": ["4273929280"],
                    "payment_method_id": "gift_card_3410768",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_gonzalez_8900",
        instruction="Your name is Yusuf Gonzalez and your zip code is 91455. You are busy, messy, patient. Cancel order #W2230795 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W2230795", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="liam_li_8526",
        instruction="Your name is Liam Li and your zip code is 28226. You are insecure, logical, cautious, independent, shy. For #W1130240, change address to {'order_id': '#W1130240', 'address1': '707 Maple Drive', 'address2': 'Suite 817', 'city': 'San Antonio', 'country': 'USA', 'state': 'TX', 'zip': '78202'} (same as #W8838515). For #W1130240, modify Dumbbell Set {'weight range': '30-50 lbs', 'material': 'urethane', 'set type': 'fixed'} to {'weight range': '5-25 lbs', 'material': 'rubber'}; via gift_card_5427896. ",
        actions=[
            Action(
                name="modify_pending_order_address",
                kwargs={
                    "order_id": "#W1130240",
                    "address1": "707 Maple Drive",
                    "address2": "Suite 817",
                    "city": "San Antonio",
                    "country": "USA",
                    "state": "TX",
                    "zip": "78202",
                },
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W1130240",
                    "item_ids": ["7159180318"],
                    "new_item_ids": ["8068777068"],
                    "payment_method_id": "gift_card_5427896",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sofia_kovacs_7075",
        instruction="Your name is Sofia Kovacs and your zip code is 19049. You are organized, patient, independent, outgoing, pessimistic. For #W5765741, modify Portable Charger {'capacity': '5000mAh', 'output': 'USB-A', 'color': 'white'} to {'capacity': '20000mAh', 'output': 'Wireless', 'color': 'black'}; via paypal_6840891. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W5765741",
                    "item_ids": ["7903094618"],
                    "new_item_ids": ["8349903180"],
                    "payment_method_id": "paypal_6840891",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="omar_khan_2363",
        instruction="Your name is Omar Khan and your email is omar.khan3563@example.com. You are direct, outgoing, independent, relaxing. Return #W6304490 via credit_card_4420174: Skateboard; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W6304490",
                    "item_ids": ["6956751343"],
                    "payment_method_id": "credit_card_4420174",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_lopez_6291",
        instruction="Your name is Ethan Lopez and your email is ethan.lopez8943@example.com. You are organized, independent, polite, curious. Cancel order #W6779827 because no longer needed. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W6779827", "reason": "no longer needed"},
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="harper_li_7655",
        instruction="Your name is Harper Li and your email is harper.li3262@example.com. You are patient, direct, confident. Return #W9495141 via gift_card_8862145: Tablet; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W9495141",
                    "item_ids": ["6501071631"],
                    "payment_method_id": "gift_card_8862145",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="noah_brown_6181",
        instruction="Your name is Noah Brown and your zip code is 80279. You are polite, rigid. Return #W7678072 via paypal_5727330: Backpack; Electric Kettle; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W7678072",
                    "item_ids": ["3557711149", "2323972008"],
                    "payment_method_id": "paypal_5727330",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="yusuf_ahmed_6232",
        instruction="Your name is Yusuf Ahmed and your email is yusuf.ahmed5476@example.com. You are organized, confident, busy, dependent, logical. Cancel order #W7007896 because ordered by mistake. For #W7756209, modify Grill {'type': 'electric', 'size': 'large', 'features': 'rotisserie'} to {'type': 'gas', 'size': 'portable', 'features': 'side burner'}; Backpack {'color': 'grey', 'size': 'small', 'material': 'nylon', 'compartment': 'laptop'} to {'size': 'large', 'material': 'polyester', 'compartment': 'hydration'}; via credit_card_2167533. ",
        actions=[
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W7007896", "reason": "ordered by mistake"},
            ),
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W7756209",
                    "item_ids": ["4404981319", "8054888773"],
                    "new_item_ids": ["9724317332", "6309044598"],
                    "payment_method_id": "credit_card_2167533",
                },
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="sophia_garcia_1101",
        instruction="Your name is Sophia Garcia and your email is sophia.garcia9791@example.com. You are impatient, rigid, direct, organized, happy. For #W1023987, exchange Pet Bed {'size': 'medium', 'material': 'memory foam', 'color': 'brown'} to {'color': 'beige'}; via gift_card_9450778. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W1023987",
                    "item_ids": ["5067898160"],
                    "new_item_ids": ["3360679910"],
                    "payment_method_id": "gift_card_9450778",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="lei_khan_6353",
        instruction="Your name is Lei Khan and your zip code is 92182. You are organized, cautious, confident, shy, busy. Return #W2787996 via gift_card_6786837: T-Shirt; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W2787996",
                    "item_ids": ["9354168549"],
                    "payment_method_id": "gift_card_6786837",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mei_hernandez_3296",
        instruction="Your name is Mei Hernandez and your email is mei.hernandez3608@example.com. You are curious, rigid, confident, logical. For #W3864587, exchange Bluetooth Speaker {'color': 'black', 'battery life': '10 hours', 'water resistance': 'no'} to {'color': 'blue', 'water resistance': 'yes'}; Mechanical Keyboard {'switch type': 'clicky', 'backlight': 'white', 'size': '80%'} to {'switch type': 'linear', 'backlight': 'none', 'size': 'full size'}; via paypal_1768431. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W3864587",
                    "item_ids": ["7597543861", "4843487907"],
                    "new_item_ids": ["4716977452", "9570044148"],
                    "payment_method_id": "paypal_1768431",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="mei_moore_8248",
        instruction="Your name is Mei Moore and your zip code is 90980. You are pessimistic, rigid, busy, insecure. Return #W9694847 via credit_card_2902980: Air Purifier; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W9694847",
                    "item_ids": ["5669664287"],
                    "payment_method_id": "credit_card_2902980",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="ethan_moore_3587",
        instruction="Your name is Ethan Moore and your zip code is 90651. You are optimistic, shy. For #W7584328, modify Backpack {'color': 'navy', 'size': 'small', 'material': 'nylon', 'compartment': 'laptop'} to {'color': 'green', 'material': 'leather', 'compartment': 'camera'}; via credit_card_6173085. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W7584328",
                    "item_ids": ["2492465580"],
                    "new_item_ids": ["7251508981"],
                    "payment_method_id": "credit_card_6173085",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="emma_santos_9753",
        instruction="Your name is Emma Santos and your zip code is 78228. You are creative, sad, curious. For #W1539823, exchange Indoor Security Camera {'resolution': '2K', 'field of view': '130 degrees', 'connectivity': 'Ethernet'} to {}; via credit_card_5869505. Cancel order #W1620235 because ordered by mistake. Cancel order #W2918688 because no longer needed. ",
        actions=[
            Action(
                name="exchange_delivered_order_items",
                kwargs={
                    "order_id": "#W1539823",
                    "item_ids": ["8470360507"],
                    "new_item_ids": ["8470360507"],
                    "payment_method_id": "credit_card_5869505",
                },
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W1620235", "reason": "ordered by mistake"},
            ),
            Action(
                name="cancel_pending_order",
                kwargs={"order_id": "#W2918688", "reason": "no longer needed"},
            ),
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="liam_li_5260",
        instruction="Your name is Liam Li and your email is liam.li2557@example.com. You are curious, relaxing, insecure, creative, outgoing. For #W9653558, modify Coffee Maker {'color': 'stainless steel', 'capacity': '4 cups', 'type': 'drip', 'features': 'built-in grinder'} to {'color': 'black', 'capacity': '2 cups', 'type': 'espresso', 'features': 'timer'}; via credit_card_7933535. ",
        actions=[
            Action(
                name="modify_pending_order_items",
                kwargs={
                    "order_id": "#W9653558",
                    "item_ids": ["1323134954"],
                    "new_item_ids": ["9862136885"],
                    "payment_method_id": "credit_card_7933535",
                },
            )
        ],
        outputs=[],
    ),
    Task(
        annotator="synthetic",
        user_id="juan_santos_1448",
        instruction="Your name is Juan Santos and your email is juan.santos3161@example.com. You are outgoing, impatient, independent, cautious. Return #W2582045 via gift_card_3767667: Air Purifier; ",
        actions=[
            Action(
                name="return_delivered_order_items",
                kwargs={
                    "order_id": "#W2582045",
                    "item_ids": ["5669664287"],
                    "payment_method_id": "gift_card_3767667",
                },
            )
        ],
        outputs=[],
    ),
]
