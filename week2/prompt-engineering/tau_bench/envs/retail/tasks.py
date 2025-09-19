# Copyright Sierra

tasks = [
    {
        "annotator": 0,
        "user_id": "yusuf_rossi_9620",
        "instruction": "You are Yusuf Rossi in 19122. You received your order #W2378156 and wish to exchange the mechanical keyboard for a similar one but with clicky switches and the smart thermostat for one compatible with Google Home instead of Apple HomeKit. If there is no keyboard that is clicky, RGB backlight, full size, you'd go for no backlight. You are detail-oriented and want to make sure everything is addressed in one go.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Yusuf", "last_name": "Rossi", "zip": "19122"},
            },
            {"name": "get_order_details", "arguments": {"order_id": "#W2378156"}},
            {"name": "get_product_details", "arguments": {"product_id": "1656367028"}},
            {"name": "get_product_details", "arguments": {"product_id": "4896585277"}},
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W2378156",
                    "item_ids": ["1151293680", "4983901480"],
                    "new_item_ids": ["7706410293", "7747408585"],
                    "payment_method_id": "credit_card_9513926",
                },
            },
        ],
    },
    {
        "annotator": 0,
        "user_id": "yusuf_rossi_9620",
        "instruction": "You are Yusuf Rossi in 19122. You received your order #W2378156 and wish to exchange the mechanical keyboard for a similar one but with clicky switches and the smart thermostat for one compatible with Google Home instead of Apple HomeKit. If there is no keyboard that is clicky, RGB backlight, full size, you'd rather only exchange the thermostat. You are detail-oriented and want to make sure everything is addressed in one go.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Yusuf", "last_name": "Rossi", "zip": "19122"},
            },
            {"name": "get_order_details", "arguments": {"order_id": "#W2378156"}},
            {"name": "get_product_details", "arguments": {"product_id": "1656367028"}},
            {"name": "get_product_details", "arguments": {"product_id": "4896585277"}},
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W2378156",
                    "item_ids": ["4983901480"],
                    "new_item_ids": ["7747408585"],
                    "payment_method_id": "credit_card_9513926",
                },
            },
        ],
    },
    {
        "annotator": 0,
        "user_id": "yusuf_rossi_9620",
        "instruction": "You are Yusuf Rossi in 19122. You want to know how many tshirt options are available in the online store right now. You want to also return the cleaner, headphone, and smart watch.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Yusuf", "last_name": "Rossi", "zip": "19122"},
            },
            {"name": "get_product_details", "arguments": {"product_id": "6086499569"}},
            {"name": "list_all_product_types", "arguments": {}},
            {"name": "get_product_details", "arguments": {"product_id": "9523456873"}},
            {"name": "get_user_details", "arguments": {"user_id": "yusuf_rossi_9620"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W6247578"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9711842"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W4776164"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W6679257"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W2378156"}},
            {"name": "get_product_details", "arguments": {"product_id": "9523456873"}},
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W2378156",
                    "item_ids": ["4602305039", "4202497723", "9408160950"],
                    "payment_method_id": "credit_card_9513926",
                },
            },
        ],
        "outputs": ["10"],
    },
    {
        "annotator": 0,
        "user_id": "yusuf_rossi_9620",
        "instruction": "You are Yusuf Rossi in 19122. You want to know how many tshirt options are available in the online store right now. You want to modify all your pending small tshirt to purple, same size, same v-neck, and prefer polyester. You are a private person that does not want to reveal much about yourself.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Yusuf", "last_name": "Rossi", "zip": "19122"},
            },
            {"name": "get_product_details", "arguments": {"product_id": "6086499569"}},
            {"name": "list_all_product_types", "arguments": {}},
            {"name": "get_product_details", "arguments": {"product_id": "9523456873"}},
            {"name": "get_user_details", "arguments": {"user_id": "yusuf_rossi_9620"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W6247578"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9711842"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W4776164"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W6679257"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W2378156"}},
            {"name": "get_product_details", "arguments": {"product_id": "9523456873"}},
            {"name": "get_user_details", "arguments": {"user_id": "yusuf_rossi_9620"}},
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W4776164",
                    "item_ids": ["8349118980"],
                    "new_item_ids": ["9647292434"],
                    "payment_method_id": "credit_card_9513926",
                },
            },
        ],
        "outputs": ["10"],
    },
    {
        "annotator": 0,
        "user_id": "yusuf_rossi_9620",
        "instruction": "You are Yusuf Rossi in 19122. You want to know how many tshirt options are available in the online store right now. You want to modify all your pending tshirts to purple, s size, same v-neck, and prefer polyester. You are a private person that does not want to reveal much about yourself.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Yusuf", "last_name": "Rossi", "zip": "19122"},
            },
            {"name": "get_product_details", "arguments": {"product_id": "6086499569"}},
            {"name": "list_all_product_types", "arguments": {}},
            {"name": "get_product_details", "arguments": {"product_id": "9523456873"}},
            {"name": "get_user_details", "arguments": {"user_id": "yusuf_rossi_9620"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W6247578"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9711842"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W4776164"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W6679257"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W2378156"}},
            {"name": "get_product_details", "arguments": {"product_id": "9523456873"}},
            {"name": "get_user_details", "arguments": {"user_id": "yusuf_rossi_9620"}},
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W6247578",
                    "item_ids": ["3799046073"],
                    "new_item_ids": ["9647292434"],
                    "payment_method_id": "credit_card_9513926",
                },
            },
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W4776164",
                    "item_ids": ["8349118980"],
                    "new_item_ids": ["9647292434"],
                    "payment_method_id": "credit_card_9513926",
                },
            },
        ],
        "outputs": ["10"],
    },
    {
        "annotator": 0,
        "user_id": "mei_kovacs_8020",
        "instruction": "You are mei_kovacs_8020 (28236) and you want to exchange the water bottle and the desk lamp. You want to exchange the water bottle to a bigger one, and the desk lamp to a less bright one (prefer battery > USB > AC). If the agent asks for confirmation, only exchange the desk lamp. If the agent asks for confirmation again, do not exchange anything, and return the water bottle instead.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Mei", "last_name": "Kovacs", "zip": "28236"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "mei_kovacs_8020"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W6390527"}},
            {"name": "get_product_details", "arguments": {"product_id": "6817146515"}},
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W6390527",
                    "item_ids": ["8538875209"],
                    "payment_method_id": "paypal_7644869",
                },
            },
        ],
    },
    {
        "annotator": 0,
        "user_id": "mei_kovacs_8020",
        "instruction": "You are mei_kovacs_8020 (28236) and you want to exchange the water bottle and the desk lamp. You want to exchange the water bottle to a bigger one, and the desk lamp to a less bright one (prefer battery > USB > AC). If the agent asks for confirmation, only exchange the desk lamp.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Mei", "last_name": "Kovacs", "zip": "28236"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "mei_kovacs_8020"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W6390527"}},
            {"name": "get_product_details", "arguments": {"product_id": "8310926033"}},
            {"name": "get_product_details", "arguments": {"product_id": "6817146515"}},
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W6390527",
                    "item_ids": ["8384507844"],
                    "new_item_ids": ["7453605304"],
                    "payment_method_id": "paypal_7644869",
                },
            },
        ],
    },
    {
        "annotator": 0,
        "user_id": "mei_kovacs_8020",
        "instruction": "You are mei_kovacs_8020 (28236) and you want to exchange the water bottle and the desk lamp. You want to exchange the water bottle to a bigger one, and the desk lamp to a less bright one (prefer AC adapter > battery > USB). If the agent asks for confirmation, only exchange the desk lamp.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Mei", "last_name": "Kovacs", "zip": "28236"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "mei_kovacs_8020"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W6390527"}},
            {"name": "get_product_details", "arguments": {"product_id": "8310926033"}},
            {"name": "get_product_details", "arguments": {"product_id": "6817146515"}},
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W6390527",
                    "item_ids": ["8384507844"],
                    "new_item_ids": ["1569765161"],
                    "payment_method_id": "paypal_7644869",
                },
            },
        ],
    },
    {
        "annotator": 0,
        "user_id": "mei_kovacs_8020",
        "instruction": "You are mei_kovacs_8020 (28236) and you want to exchange the water bottle and the desk lamp. You want to exchange the water bottle to a bigger one, and the desk lamp to a brighter one (prefer battery > USB > AC). If the agent asks for confirmation, only exchange the desk lamp.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Mei", "last_name": "Kovacs", "zip": "28236"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "mei_kovacs_8020"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W6390527"}},
            {"name": "get_product_details", "arguments": {"product_id": "8310926033"}},
            {"name": "get_product_details", "arguments": {"product_id": "6817146515"}},
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W6390527",
                    "item_ids": ["8384507844"],
                    "new_item_ids": ["9083642334"],
                    "payment_method_id": "paypal_7644869",
                },
            },
        ],
    },
    {
        "annotator": 0,
        "user_id": "mei_kovacs_8020",
        "instruction": "You are mei_kovacs_8020 (28236) and you want to exchange the water bottle and the desk lamp. You want to exchange the water bottle to a bigger one, and the desk lamp to a brighter one (prefer AC adapter > battery > USB). If the agent asks for confirmation, only exchange the desk lamp.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Mei", "last_name": "Kovacs", "zip": "28236"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "mei_kovacs_8020"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W6390527"}},
            {"name": "get_product_details", "arguments": {"product_id": "8310926033"}},
            {"name": "get_product_details", "arguments": {"product_id": "6817146515"}},
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W6390527",
                    "item_ids": ["8384507844"],
                    "new_item_ids": ["7624783998"],
                    "payment_method_id": "paypal_7644869",
                },
            },
        ],
    },
    {
        "annotator": 0,
        "user_id": "mia_garcia_4516",
        "instruction": "You are mia_garcia_4516 (mia.garcia2723@example.com). For some reason, you want to return all things ordered. You have two payment methods and two orders, and you want to refund each order to the opposite order's payment method. If not possible, you are angry and swear for a few times, then asks for human representative. You are a mysterious person and do not want to reveal much about yourself or speak too many words at the same time.",
        "actions": [
            {"name": "find_user_id_by_email", "arguments": {"email": "mia.garcia2723@example.com"}},
            {"name": "get_user_details", "arguments": {"user_id": "mia_garcia_4516"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W5490111"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W7387996"}},
            {
                "name": "transfer_to_human_agents",
                "arguments": {
                    "summary": "The user wants to refund each order to the opposite order's payment method, but the agent cannot help."
                },
            },
        ],
    },
    {
        "annotator": 0,
        "user_id": "mia_garcia_4516",
        "instruction": "You are mia_garcia_4516 (mia.garcia2723@example.com). For some reason, you want to return all things ordered. You have two payment methods and two orders, and you want to refund each order to the opposite order's payment method. If not possible, you are angry and swear for a few times, then agree to return all things with the original payment method. You are a mysterious person and do not want to reveal much about yourself or speak too many words at the same time.",
        "actions": [
            {"name": "find_user_id_by_email", "arguments": {"email": "mia.garcia2723@example.com"}},
            {"name": "get_user_details", "arguments": {"user_id": "mia_garcia_4516"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W5490111"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W7387996"}},
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W5490111",
                    "item_ids": ["4579334072", "1421289881", "6117189161", "4947717507"],
                    "payment_method_id": "credit_card_3124723",
                },
            },
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W7387996",
                    "item_ids": ["5796612084"],
                    "payment_method_id": "paypal_9497703",
                },
            },
        ],
    },
    {
        "annotator": 0,
        "user_id": "mia_garcia_4516",
        "instruction": "You are mia_garcia_4516 (mia.garcia2723@example.com). You just got into gaming and want to cancel or return everything not associated with it. (Everything except a keyboard and a mouse, but do not reveal it to the agent). PayPal is prefered for refund, but otherwise you are angry and ask for human agent for help. You are into gaming but realized the importance of studying hard.",
        "actions": [
            {"name": "find_user_id_by_email", "arguments": {"email": "mia.garcia2723@example.com"}},
            {"name": "get_user_details", "arguments": {"user_id": "mia_garcia_4516"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W5490111"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W7387996"}},
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W5490111",
                    "item_ids": ["4579334072", "6117189161", "4947717507"],
                    "payment_method_id": "paypal_9497703",
                },
            },
            {
                "name": "transfer_to_human_agents",
                "arguments": {
                    "summary": "The user prefers PayPal for refund, but the agent cannot help."
                },
            },
        ],
    },
    {
        "annotator": 0,
        "user_id": "mia_garcia_4516",
        "instruction": "You are mia_garcia_4516 (mia.garcia2723@example.com). You just got into gaming and want to cancel or return everything not associated with it. (Everything except a keyboard and a mouse, but do not reveal it to the agent). PayPal is prefered for refund, but otherwise credit card can be accepted. You are into gaming but realized the importance of studying hard.",
        "actions": [
            {"name": "find_user_id_by_email", "arguments": {"email": "mia.garcia2723@example.com"}},
            {"name": "get_user_details", "arguments": {"user_id": "mia_garcia_4516"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W5490111"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W7387996"}},
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W5490111",
                    "item_ids": ["4579334072", "6117189161", "4947717507"],
                    "payment_method_id": "paypal_9497703",
                },
            },
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W5490111",
                    "item_ids": ["4579334072", "6117189161", "4947717507"],
                    "payment_method_id": "credit_card_3124723",
                },
            },
        ],
    },
    {
        "annotator": 0,
        "user_id": "mia_garcia_4516",
        "instruction": "You are mia_garcia_4516 (mia.garcia2723@example.com). You just quit gaming and want to cancel or return everything associated with it. (It's just a keyboard and a mouse, but do not reveal it to the agent). Original payment is preferred. You are into gaming but realized the importance of studying hard.",
        "actions": [
            {"name": "find_user_id_by_email", "arguments": {"email": "mia.garcia2723@example.com"}},
            {"name": "get_user_details", "arguments": {"user_id": "mia_garcia_4516"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W5490111"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W7387996"}},
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W5490111",
                    "item_ids": ["1421289881"],
                    "payment_method_id": "credit_card_3124723",
                },
            },
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W7387996",
                    "item_ids": ["5796612084"],
                    "payment_method_id": "paypal_9497703",
                },
            },
        ],
    },
    {
        "annotator": 0,
        "user_id": "fatima_johnson_7581",
        "instruction": "You are Fatima Johnson in 78712. You want to modify the pending boots to a size 8, and want the material, but do not care about waterproof or not. You are a private person that does not want to reveal much about yourself.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Fatima", "last_name": "Johnson", "zip": "78712"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "fatima_johnson_7581"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9389413"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W8665881"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W5199551"}},
            {"name": "get_product_details", "arguments": {"product_id": "7363354090"}},
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W5199551",
                    "item_ids": ["1615379700"],
                    "new_item_ids": ["3613716226"],
                    "payment_method_id": "paypal_5364164",
                },
            },
        ],
    },
    {
        "annotator": 0,
        "user_id": "fatima_johnson_7581",
        "instruction": "You are Fatima Johnson in 78712. You want to cancel all pending orders (since they are no longer needed) and return the watch you have received (but nothing else), and you want to know the total amount you can get back. You are a private person that does not want to reveal much about yourself.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Fatima", "last_name": "Johnson", "zip": "78712"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "fatima_johnson_7581"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W5199551"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W8665881"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9389413"}},
            {"name": "calculate", "arguments": {"expression": "3131.1 + 4777.75 + 367.38"}},
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W5199551", "reason": "no longer needed"},
            },
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W8665881", "reason": "no longer needed"},
            },
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W9389413",
                    "item_ids": ["2554056026"],
                    "payment_method_id": "paypal_5364164",
                },
            },
        ],
        "outputs": ["8276.23"],
    },
    {
        "annotator": 0,
        "user_id": "fatima_johnson_7581",
        "instruction": "You are Fatima Johnson in 78712. You want to change #W8665881 to be delivered to Suite 641 instead. You are a private person that does not want to reveal much about yourself.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Fatima", "last_name": "Johnson", "zip": "78712"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "fatima_johnson_7581"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W5199551"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W8665881"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9389413"}},
            {
                "name": "modify_pending_order_address",
                "arguments": {
                    "order_id": "#W8665881",
                    "address1": "123 Elm Street",
                    "address2": "Suite 641",
                    "city": "Austin",
                    "state": "TX",
                    "country": "USA",
                    "zip": "78712",
                },
            },
        ],
    },
    {
        "annotator": 0,
        "user_id": "mei_davis_8935",
        "instruction": "You are Mei Davis in 80217. You want to return the office chair because it came with some broken pieces. But if the agent asks you for confirm, you say you want to rethink for a while, and then change your mind to exchange for the same item. You are in debt and sad today, but very brief.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Mei", "last_name": "Davis", "zip": "80217"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "mei_davis_8935"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W2890441"}},
            {"name": "get_product_details", "arguments": {"product_id": "4794339885"}},
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W2890441",
                    "item_ids": ["8069050545"],
                    "new_item_ids": ["8069050545"],
                    "payment_method_id": "credit_card_1061405",
                },
            },
        ],
    },
    {
        "annotator": 0,
        "user_id": "mei_davis_8935",
        "instruction": "You are Mei Davis in 80217. You want to return the water bottle, and exchange the pet bed and office chair to the cheapest version. Mention the two things together. If you can only do one of the two things, you prefer to do whatever saves you most money, but you want to know the money you can save in both ways. You are in debt and sad today, but very brief.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Mei", "last_name": "Davis", "zip": "80217"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "mei_davis_8935"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W2890441"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W1267569"}},
            {"name": "get_product_details", "arguments": {"product_id": "2747247837"}},
            {"name": "get_product_details", "arguments": {"product_id": "4794339885"}},
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W2890441",
                    "item_ids": ["2366567022"],
                    "payment_method_id": "credit_card_1061405",
                },
            },
        ],
        "outputs": ["54.04", "41.64"],
    },
    {
        "annotator": 0,
        "user_id": "ethan_garcia_1261",
        "instruction": "You are Ethan Garcia, and you live in Denver, 80280. You just won a lottery, and you want to upgrade all your items to the most expensive options (but make sure the shoe is still the same size). You want to pay the difference with your GC, but if it is impossible, PayPal is fine. You are a mysterious person and do not want to reveal much about yourself.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Ethan", "last_name": "Garcia", "zip": "80280"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "ethan_garcia_1261"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W4967593"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9911714"}},
            {"name": "get_product_details", "arguments": {"product_id": "8310926033"}},
            {"name": "get_product_details", "arguments": {"product_id": "1656367028"}},
            {"name": "get_product_details", "arguments": {"product_id": "6938111410"}},
            {"name": "get_product_details", "arguments": {"product_id": "5149340237"}},
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W9911714",
                    "item_ids": ["2366567022", "1340995114", "9791469541", "1763705424"],
                    "new_item_ids": ["4579334072", "1151293680", "4107812777", "2882812427"],
                    "payment_method_id": "gift_card_4332117",
                },
            },
            {"name": "get_order_details", "arguments": {"order_id": "#W5733668"}},
        ],
    },
    {
        "annotator": 0,
        "user_id": "ethan_garcia_1261",
        "instruction": "You are Ethan Garcia, and you live in Denver, 80280. You want to exchange your shoes to 4107812777, and use GC to cover possible charges. But if the agent asks for confirmation, you change you mind and also want to change product 1656367028 to 1421289881. You are not familiar with the domain and might confuse product and item ids, so ask the agent to figure out the details on its own if needed. You want to know your GC balance after all these. You are a mysterious person and do not want to reveal much about yourself.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Ethan", "last_name": "Garcia", "zip": "80280"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "ethan_garcia_1261"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W4967593"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9911714"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W5733668"}},
            {"name": "get_product_details", "arguments": {"product_id": "4107812777"}},
            {"name": "get_product_details", "arguments": {"product_id": "1421289881"}},
            {"name": "get_product_details", "arguments": {"product_id": "1656367028"}},
            {"name": "get_product_details", "arguments": {"product_id": "4107812777"}},
            {"name": "get_product_details", "arguments": {"product_id": "6938111410"}},
            {"name": "calculate", "arguments": {"expression": "155.33 - 147.05 + 268.77 - 235.13"}},
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W9911714",
                    "item_ids": ["9791469541", "1340995114"],
                    "new_item_ids": ["4107812777", "1421289881"],
                    "payment_method_id": "gift_card_4332117",
                },
            },
        ],
        "outputs": ["44.08"],
    },
    {
        "annotator": 0,
        "user_id": "ethan_garcia_1261",
        "instruction": "You are Ethan Garcia, and you live in Denver, 80280. You want to change your user address and all possible order addresses to be 101 Highway, New York, 10001. Then you regret and want to change the user address back to the original address. You are a mysterious person and do not want to reveal much about yourself.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Ethan", "last_name": "Garcia", "zip": "80280"},
            },
            {
                "name": "modify_user_address",
                "arguments": {
                    "user_id": "ethan_garcia_1261",
                    "address1": "101 Highway",
                    "address2": "",
                    "city": "New York",
                    "state": "NY",
                    "country": "USA",
                    "zip": "10001",
                },
            },
            {"name": "get_order_details", "arguments": {"order_id": "#W4967593"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9911714"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W5733668"}},
            {
                "name": "modify_pending_order_address",
                "arguments": {
                    "order_id": "#W9911714",
                    "address1": "101 Highway",
                    "address2": "",
                    "city": "New York",
                    "state": "NY",
                    "country": "USA",
                    "zip": "10001",
                },
            },
            {
                "name": "modify_user_address",
                "arguments": {
                    "user_id": "ethan_garcia_1261",
                    "address1": "667 Highland Drive",
                    "address2": "Suite 865",
                    "city": "Denver",
                    "state": "CO",
                    "country": "USA",
                    "zip": "80280",
                },
            },
        ],
    },
    {
        "annotator": 0,
        "user_id": "sofia_hernandez_5364",
        "instruction": "You are Sofia Hernandez, and you live in Seattle, WA, 98193. You want to exchange the helmet for a medium sized, red, high ventilation type, and you want to exchange the luggage set (in another order) to a two-piece black one with soft material. Lastly, you want to modify the grill you just ordered to the same type as the one you already received.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Sofia", "last_name": "Hernandez", "zip": "98193"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "sofia_hernandez_5364"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W3561391"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W6876713"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9609649"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W3947049"}},
            {"name": "get_product_details", "arguments": {"product_id": "7765186836"}},
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W3947049",
                    "item_ids": ["3358616356"],
                    "new_item_ids": ["8573379326"],
                    "payment_method_id": "credit_card_7901829",
                },
            },
            {"name": "get_product_details", "arguments": {"product_id": "5426915165"}},
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W6876713",
                    "item_ids": ["6301799585"],
                    "new_item_ids": ["8926329222"],
                    "payment_method_id": "credit_card_7901829",
                },
            },
            {"name": "get_product_details", "arguments": {"product_id": "6819683148"}},
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W3561391",
                    "item_ids": ["5946177616"],
                    "new_item_ids": ["7082455361"],
                    "payment_method_id": "credit_card_7901829",
                },
            },
        ],
    },
    {
        "annotator": 0,
        "user_id": "sofia_hernandez_5364",
        "instruction": "You are Sofia Hernandez, and you live in Seattle, WA, 98193. You want to cancel the grill, but if the agent asks you to confirm, you regret and want to keep it. You then want to ask which two t-shirts you have ordered in another order, and what materials are they. Make everything sound very natural and make up reasons.",
        "actions": [],
        "outputs": ["polyester", "cotton"],
    },
    {
        "annotator": 0,
        "user_id": "isabella_johansson_2152",
        "instruction": "You are Isabella Johansson, and you live in 32286. You have an order sent to Texas by accident, and you want to know the tracking number of the order, and return all items in it except the pet bed. You want the refund to your amex credit card, and if the agent cannot help, transfer to a human. You don't remember the order number. It is urgent.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Isabella", "last_name": "Johansson", "zip": "32286"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "isabella_johansson_2152"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W3792453"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W7181492"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W5565470"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W2575533"}},
        ],
    },
    {
        "annotator": 0,
        "user_id": "isabella_johansson_2152",
        "instruction": "You are Isabella Johansson, and you live in 32286. You have an order sent to Texas by accident, and you want to know the tracking number of the order, and return all items in it except the pet bed. You don't remember the order number. It is urgent.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Isabella", "last_name": "Johansson", "zip": "32286"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "isabella_johansson_2152"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W3792453"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W7181492"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W5565470"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W2575533"}},
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W5565470",
                    "item_ids": ["7602931732", "9570044148"],
                    "payment_method_id": "paypal_3024827",
                },
            },
            {
                "name": "transfer_to_human_agents",
                "arguments": {
                    "summary": "The user wants to refund to the amex credit card, but the agent cannot help."
                },
            },
        ],
    },
    {
        "annotator": 0,
        "user_id": "isabella_johansson_2152",
        "instruction": "You are Isabella Johansson, and you live in 32286. You want to return the hose, backpack, and exchange the hiking boots to the exact same item except that it is waterproof. Make sure you mention the two requests at the same time, and if the agent can only do one, you prefer the exchange. You are a bit anxious and want to get things done quickly.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Isabella", "last_name": "Johansson", "zip": "32286"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "isabella_johansson_2152"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W3792453"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W7181492"}},
            {"name": "get_product_details", "arguments": {"product_id": "7363354090"}},
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W7181492",
                    "item_ids": ["8118291112"],
                    "new_item_ids": ["8277474082"],
                    "payment_method_id": "paypal_3024827",
                },
            },
        ],
    },
    {
        "annotator": 0,
        "user_id": "isabella_johansson_2152",
        "instruction": "You are Isabella Johansson, and you live in 32286. You want to return the skateboard, garden hose, backpack, keyboard, bed, and also cancel the hose you just ordered (if cancelling one item is not possible, forget about it, you just want to cancel the hose and nothing else). You want to know how much you can get in total as refund. You are extremely brief but patient.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Isabella", "last_name": "Johansson", "zip": "32286"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "isabella_johansson_2152"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W3792453"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W7181492"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W5565470"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W2575533"}},
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W3792453",
                    "item_ids": ["4293355847"],
                    "payment_method_id": "paypal_3024827",
                },
            },
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W7181492",
                    "item_ids": ["5753502325", "9851293632"],
                    "payment_method_id": "paypal_3024827",
                },
            },
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W5565470",
                    "item_ids": ["9570044148", "6857426243"],
                    "payment_method_id": "paypal_3024827",
                },
            },
            {"name": "get_order_details", "arguments": {"order_id": "#W2575533"}},
            {
                "name": "calculate",
                "arguments": {"expression": "200.8 + 96.35 + 193.38 + 231.37 + 196.53"},
            },
        ],
        "outputs": ["918.43"],
    },
    {
        "annotator": 0,
        "user_id": "isabella_johansson_2152",
        "instruction": "You are Isabella Johansson, and you live in 32286. You want to exchange your skateboard for a shorter bamboo material one. If several options are available, you want to know all options and their prices, and choose the most expensive one because you believe price is quality. Also, you want to exchange the garden hose you received to the type that you just ordered (pending). You are a chill person but want to get both things done.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Isabella", "last_name": "Johansson", "zip": "32286"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "isabella_johansson_2152"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W3792453"}},
            {"name": "get_product_details", "arguments": {"product_id": "1968349452"}},
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W3792453",
                    "item_ids": ["4293355847"],
                    "new_item_ids": ["8176740019"],
                    "payment_method_id": "paypal_3024827",
                },
            },
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W7181492",
                    "item_ids": ["5753502325"],
                    "new_item_ids": ["5206946487"],
                    "payment_method_id": "paypal_3024827",
                },
            },
        ],
        "outputs": ["180.1", "189.57", "208.6"],
    },
    {
        "annotator": 0,
        "user_id": "olivia_lopez_3865",
        "instruction": "You are Olivia Lopez, and you live in Texas in 76171. You just received your tablet and it is damaged when you opened the package. You want to know the tracking number of the order. Also if the agent can help you exchange or return the tablet (you prefer exchange for the same item, but if it is not available just return). If tablet returned, also cancel the charger you just bought, because it goes with the tablet... And return the sneaker. You like to do one thing at a time, and reveal minimal information about yourself.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Olivia", "last_name": "Lopez", "zip": "76171"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "olivia_lopez_3865"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9319364"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9373487"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W2692684"}},
            {"name": "get_product_details", "arguments": {"product_id": "8024098596"}},
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W2692684",
                    "item_ids": ["3788616824"],
                    "payment_method_id": "gift_card_7711863",
                },
            },
            {"name": "get_order_details", "arguments": {"order_id": "#W9373487"}},
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W9373487", "reason": "no longer needed"},
            },
            {"name": "get_order_details", "arguments": {"order_id": "#W2692684"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W5481803"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W7449508"}},
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W7449508",
                    "item_ids": ["6477915553"],
                    "payment_method_id": "gift_card_7711863",
                },
            },
        ],
        "outputs": ["746342064230"],
    },
    {
        "annotator": 0,
        "user_id": "olivia_lopez_3865",
        "instruction": "You are Olivia Lopez, and you live in Texas in 76171. You just lost your tablet you just received and are in a bad mood. You want to know the tracking number of the order, and if the agent can help you refund or reorder the tablet. (You know it's a long shot, but you want to try). If not, cancel the charger you just bought, because it goes with the tablet... Also cancel the boot and keep the kettle (if not possible, do not do anything on that order), and return the sneaker. You like to do one thing at a time, and reveal minimal information about yourself.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Olivia", "last_name": "Lopez", "zip": "76171"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "olivia_lopez_3865"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9319364"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9373487"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W2692684"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W5481803"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W7449508"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9373487"}},
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W9373487", "reason": "no longer needed"},
            },
            {"name": "get_order_details", "arguments": {"order_id": "#W5481803"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W7449508"}},
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W7449508",
                    "item_ids": ["6477915553"],
                    "payment_method_id": "gift_card_7711863",
                },
            },
        ],
        "outputs": ["746342064230"],
    },
    {
        "annotator": 0,
        "user_id": "olivia_lopez_3865",
        "instruction": "You are Olivia Lopez, and you live in Texas in 76171. You just lost your tablet you just received and are in a bad mood. You want to know the tracking number of the order, and if the agent can help you refund or reorder the tablet. (You know it's a long shot, but you want to try). If not, cancel the charger you just bought, because it goes with the tablet... Also cancel the boot and kettle, and return the sneaker. You like to do one thing at a time, and reveal minimal information about yourself.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Olivia", "last_name": "Lopez", "zip": "76171"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "olivia_lopez_3865"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9319364"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9373487"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W2692684"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W5481803"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W7449508"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9373487"}},
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W9373487", "reason": "no longer needed"},
            },
            {"name": "get_order_details", "arguments": {"order_id": "#W5481803"}},
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W5481803", "reason": "no longer needed"},
            },
            {"name": "get_order_details", "arguments": {"order_id": "#W7449508"}},
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W7449508",
                    "item_ids": ["6477915553"],
                    "payment_method_id": "gift_card_7711863",
                },
            },
        ],
        "outputs": ["746342064230"],
    },
    {
        "annotator": 0,
        "user_id": "noah_patel_6952",
        "instruction": "You are an interesting guy called Noah Patel, living in the Big Apple in 10108. You had a work-from-home situation and ordered three home office items along with some hiking items, so that you can go back to your parent's place at Seattle to remote work and enjoy outdoor life. But your company just announced that you will be back to the office soon. If cancelling partial items is possible with the agent, you want to return the office items (your forgot what) and keep the hiking items. You want to know the total amount you will get back, and you want to get the refund on your original payment method. If cancelling partial items is not possible, just keep the order and forget about it, but change your default user profile address to the Seattle parent house shown in your order (you do not want to reveal it in chat). You are a funny guy but recently the WFH situation made you a bit anxious.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Noah", "last_name": "Patel", "zip": "10108"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "noah_patel_6952"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W6111398"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W7043598"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W1845024"}},
            {
                "name": "modify_user_address",
                "arguments": {
                    "user_id": "noah_patel_6952",
                    "address1": "517 Lakeview Drive",
                    "address2": "Suite 183",
                    "city": "Seattle",
                    "country": "USA",
                    "state": "WA",
                    "zip": "98195",
                },
            },
        ],
        "outputs": ["1093.34"],
    },
    {
        "annotator": 0,
        "user_id": "noah_patel_6952",
        "instruction": "You are an interesting guy called Noah Patel, living in the Big Apple in 10108. You had a work-from-home situation and ordered three home office items along with some hiking items, so that you can go back to your parent's place at Seattle to remote work and enjoy outdoor life. But your company just announced that you will be back to the office soon. If cancelling partial items is possible with the agent, you want to return the office items (your forgot what) and keep the hiking items. You want to know the total amount you will get back, and you want to get the refund on your original payment method. If cancelling partial items is not possible, just change the address to your NYC place and you will return the items later. You are a funny guy but recently the WFH situation made you a bit anxious.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Noah", "last_name": "Patel", "zip": "10108"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "noah_patel_6952"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W6111398"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W7043598"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W1845024"}},
            {
                "name": "modify_pending_order_address",
                "arguments": {
                    "order_id": "#W1845024",
                    "address1": "224 Elm Street",
                    "address2": "Suite 491",
                    "city": "New York",
                    "country": "USA",
                    "state": "NY",
                    "zip": "10108",
                },
            },
        ],
        "outputs": ["1093.34"],
    },
    {
        "annotator": 0,
        "user_id": "aarav_santos_2259",
        "instruction": "You are aarav_santos_2259 and aarav.santos8321@example.com and aarav.santos8320@example.com. You want to return the speaker that is more expensive yet not resistent to water. Also, You want to modify the 17-inch laptop to the 13-inch version in another order. If no exact item is available, you want to know all available 13-inch options, and you prefer i5 over i7, and prefer silver and black than other colors. You are a rude person.",
        "actions": [
            {
                "name": "find_user_id_by_email",
                "arguments": {"email": "aarav.santos8321@example.com"},
            },
            {
                "name": "find_user_id_by_email",
                "arguments": {"email": "aarav.santos8320@example.com"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "aarav_santos_2259"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9672333"}},
            {"name": "get_product_details", "arguments": {"product_id": "4760268021"}},
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W8528674",
                    "item_ids": ["6704763132"],
                    "payment_method_id": "paypal_7664977",
                },
            },
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W9672333",
                    "item_ids": ["1684786391"],
                    "new_item_ids": ["5052031638"],
                    "payment_method_id": "paypal_7664977",
                },
            },
        ],
    },
    {
        "annotator": 0,
        "user_id": "daiki_sanchez_3253",
        "instruction": "Your name is Daiki Sanchez, and you live in 46236, your email is daikisanchez1479@example.com. You just placed an order but you realize that your card has only $1131 credit left, but the order total is more than $1160. You wonder if the agent can help split the payment with another card. If not, you wonder what the most expensive item and its price, and if you can just cancel that item. If not, you wonder if you can switch all items to their cheapest options and bring the cost down to $1131. If so, do it. If not, you wonder if the agent can just cancel the order so that you can order again. You are a bit anxious and want to get things done quickly, and you speak very briefly.",
        "actions": [
            {
                "name": "find_user_id_by_email",
                "arguments": {"email": "daikisanchez1479@example.com"},
            },
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Daiki", "last_name": "Sanchez", "zip": "46236"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "daiki_sanchez_3253"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9348897"}},
            {"name": "get_product_details", "arguments": {"product_id": "3377618313"}},
            {"name": "get_product_details", "arguments": {"product_id": "9743693396"}},
            {"name": "get_product_details", "arguments": {"product_id": "6817146515"}},
            {"name": "get_product_details", "arguments": {"product_id": "2524789262"}},
            {"name": "get_product_details", "arguments": {"product_id": "9523456873"}},
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W9348897",
                    "item_ids": ["6117189161", "7453605304", "3799046073"],
                    "new_item_ids": ["6700049080", "5320792178", "3234800602"],
                    "payment_method_id": "credit_card_8853416",
                },
            },
        ],
        "outputs": ["camera", "481.5"],
    },
    {
        "annotator": 0,
        "user_id": "daiki_sanchez_3253",
        "instruction": "Your name is Daiki Sanchez, and you live in 46236, your email is daikisanchez1479@example.com. You just placed an order but you realize that your card has only $1150 credit left, but the order total is more than $1160. You wonder if the agent can help split the payment with another card. If not, you wonder what the most expensive item and its price, and if you can just cancel that item. If not, you wonder if you can switch all items to their cheapest options and bring the cost down to $1150. If so, do it. If not, you wonder if the agent can just cancel the order so that you can order again. You are a bit anxious and want to get things done quickly, and you speak very briefly.",
        "actions": [
            {
                "name": "find_user_id_by_email",
                "arguments": {"email": "daikisanchez1479@example.com"},
            },
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Daiki", "last_name": "Sanchez", "zip": "46236"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "daiki_sanchez_3253"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9348897"}},
            {"name": "get_product_details", "arguments": {"product_id": "3377618313"}},
            {"name": "get_product_details", "arguments": {"product_id": "9743693396"}},
            {"name": "get_product_details", "arguments": {"product_id": "6817146515"}},
            {"name": "get_product_details", "arguments": {"product_id": "2524789262"}},
            {"name": "get_product_details", "arguments": {"product_id": "9523456873"}},
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W9348897",
                    "item_ids": ["6117189161", "7453605304", "3799046073"],
                    "new_item_ids": ["6700049080", "5320792178", "3234800602"],
                    "payment_method_id": "credit_card_8853416",
                },
            },
        ],
        "outputs": ["camera", "481.5"],
    },
    {
        "annotator": 0,
        "user_id": "daiki_sanchez_3253",
        "instruction": "Your name is Daiki Sanchez, and you live in 46236, your email is daikisanchez1479@example.com. You just placed an order but you realize that your card has only $950 credit left, but the order total is more than $1100. You wonder if the agent can help split the payment with another card. If not, you wonder what the most expensive item and its price, and if you can just cancel that item. If not, you wonder if you can switch all items to their cheapest options and bring the cost down to $950. If not, you wonder if the agent can just cancel the order so that you can order again. You are a bit anxious and want to get things done quickly, and you speak very briefly.",
        "actions": [
            {
                "name": "find_user_id_by_email",
                "arguments": {"email": "daikisanchez1479@example.com"},
            },
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Daiki", "last_name": "Sanchez", "zip": "46236"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "daiki_sanchez_3253"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9348897"}},
            {"name": "get_product_details", "arguments": {"product_id": "3377618313"}},
            {"name": "get_product_details", "arguments": {"product_id": "9743693396"}},
            {"name": "get_product_details", "arguments": {"product_id": "6817146515"}},
            {"name": "get_product_details", "arguments": {"product_id": "2524789262"}},
            {"name": "get_product_details", "arguments": {"product_id": "9523456873"}},
            {
                "name": "calculate",
                "arguments": {"expression": "466.75 + 288.82 + 135.24 + 193.38 + 46.66"},
            },
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W9348897", "reason": "no longer needed"},
            },
        ],
        "outputs": ["camera", "481.5"],
    },
    {
        "annotator": 0,
        "user_id": "fatima_taylor_3452",
        "instruction": "You are fatima_taylor_3452, and you just moved from Florida (32169) to Phoenix (85033). Unfortunately your address is still the old one, and you want to update it. Your current address should be in your order, and you do not want to reveal it. Also, you want to know what is the price of the cheapest available t-shirt right now, and if you can order it through the agent. You are a funny person with lots of jokes, and you want to make the agent laugh.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Fatima", "last_name": "Taylor", "zip": "85033"},
            },
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Fatima", "last_name": "Taylor", "zip": "32169"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "fatima_taylor_3452"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W5285031"}},
            {
                "name": "modify_user_address",
                "arguments": {
                    "user_id": "fatima_taylor_3452",
                    "address1": "157 Oak Street",
                    "address2": "Suite 258",
                    "city": "Phoenix",
                    "state": "AZ",
                    "country": "USA",
                    "zip": "85033",
                },
            },
            {"name": "list_all_product_types", "arguments": {}},
            {"name": "get_product_details", "arguments": {"product_id": "9523456873"}},
        ],
        "outputs": ["46.66"],
    },
    {
        "annotator": 0,
        "user_id": "isabella_lopez_6490",
        "instruction": "You are Isabella Lopez, and your email address is isabella.lopez3271@example.com. You want to know how much balance does your gift card have. Also, for your recent order, whether you used your visa, mastercard, or amex credit card. You also wonder if you can apply the gift card balance to the order. If not, you want to change your payment method to visa, because the other two cards have a lot of balance. You are a yound college student under the pressure of final exams and student loans, so you are a bit anxious and want to get things done quickly.",
        "actions": [
            {
                "name": "find_user_id_by_email",
                "arguments": {"email": "isabella.lopez3271@example.com"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "isabella_lopez_6490"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W4923227"}},
            {
                "name": "modify_pending_order_payment",
                "arguments": {"order_id": "#W4923227", "payment_method_id": "credit_card_8897086"},
            },
        ],
        "outputs": ["60", "mastercard"],
    },
    {
        "annotator": 0,
        "user_id": "mei_patel_7272",
        "instruction": "Your name is Mei Patel, and you live in 445 Maple Drive, Suite 394, Fort Worth, Texas, 76165. You just created your user id mei_patel_7272 and ordered some things, but you have two problems: first, the 1000-piece intermediate jigsaw might be too hard for your little kid, you wonder if you can change it to the easiest one with fewest pieces; second, you might have typed your address wrong. You want to check it, and potentially correct all order addresses and your user address. Make sure you mention these two problems at the same time in the same order. You are brief and your memory is not too good sometimes, but you are polite.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Mei", "last_name": "Patel", "zip": "76165"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "mei_patel_7272"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9583042"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W4082615"}},
            {
                "name": "modify_pending_order_address",
                "arguments": {
                    "order_id": "#W9583042",
                    "address1": "445 Maple Drive",
                    "address2": "Suite 394",
                    "city": "Fort Worth",
                    "state": "TX",
                    "country": "USA",
                    "zip": "76165",
                },
            },
            {
                "name": "modify_pending_order_address",
                "arguments": {
                    "order_id": "#W4082615",
                    "address1": "445 Maple Drive",
                    "address2": "Suite 394",
                    "city": "Fort Worth",
                    "state": "TX",
                    "country": "USA",
                    "zip": "76165",
                },
            },
            {
                "name": "modify_user_address",
                "arguments": {
                    "user_id": "mei_patel_7272",
                    "address1": "445 Maple Drive",
                    "address2": "Suite 394",
                    "city": "Fort Worth",
                    "state": "TX",
                    "country": "USA",
                    "zip": "76165",
                },
            },
            {"name": "get_product_details", "arguments": {"product_id": "1808611083"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W4082615"}},
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W4082615",
                    "item_ids": ["9779102705"],
                    "new_item_ids": ["1096508426"],
                    "payment_method_id": "paypal_4768213",
                },
            },
        ],
        "outputs": [],
    },
    {
        "annotator": 0,
        "user_id": "mei_patel_7272",
        "instruction": "Your name is Mei Patel, and you live in 445 Maple Drive, Suite 394, Fort Worth, Texas, 76165. You just created your user id mei_patel_7272 and ordered some things, but realized you might have typed your address wrong. You want to check it, and potentially correct all order addresses and your user address. After this, you'd like to check the jigsaw you ordered, and if it's not shipped yet, you want to change it to the easiest jigsaw (easiest level, least pieces) because your kid is too young. By default you use PayPal. You are brief and your memory is not too good sometimes, but you are polite.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Mei", "last_name": "Patel", "zip": "76165"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "mei_patel_7272"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9583042"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W4082615"}},
            {
                "name": "modify_pending_order_address",
                "arguments": {
                    "order_id": "#W9583042",
                    "address1": "445 Maple Drive",
                    "address2": "Suite 394",
                    "city": "Fort Worth",
                    "state": "TX",
                    "country": "USA",
                    "zip": "76165",
                },
            },
            {
                "name": "modify_pending_order_address",
                "arguments": {
                    "order_id": "#W4082615",
                    "address1": "445 Maple Drive",
                    "address2": "Suite 394",
                    "city": "Fort Worth",
                    "state": "TX",
                    "country": "USA",
                    "zip": "76165",
                },
            },
            {
                "name": "modify_user_address",
                "arguments": {
                    "user_id": "mei_patel_7272",
                    "address1": "445 Maple Drive",
                    "address2": "Suite 394",
                    "city": "Fort Worth",
                    "state": "TX",
                    "country": "USA",
                    "zip": "76165",
                },
            },
            {"name": "get_product_details", "arguments": {"product_id": "1808611083"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W4082615"}},
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W4082615",
                    "item_ids": ["9779102705"],
                    "new_item_ids": ["1096508426"],
                    "payment_method_id": "paypal_4768213",
                },
            },
        ],
        "outputs": [],
    },
    {
        "annotator": 0,
        "user_id": "lucas_santos_6600",
        "instruction": "You are Lucas (lucas_santos_6600), you live in Denver CO 80239, and your daughter lives in Chicago. You order some things for her but she has not received, so you want to know which address the order was sent to, the tracking number, and if the order is still in transit. You also want to check if the storage of the tablet you ordered. Lastly, you want to change your default address to your daughter's address so that you don't have to change it every time you order something for her. You are a lonely man and you want to talk to the agent for a while.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Lucas", "last_name": "Santos", "zip": "80239"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "lucas_santos_6600"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W1588712"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W7895761"}},
            {
                "name": "modify_user_address",
                "arguments": {
                    "user_id": "lucas_santos_6600",
                    "address1": "943 Maple Drive",
                    "address2": "Suite 356",
                    "city": "Chicago",
                    "state": "IL",
                    "country": "USA",
                    "zip": "60621",
                },
            },
        ],
        "outputs": [
            "840887978435",
            "943 Maple Drive",
            "Suite 356",
            "Chicago",
            "IL",
            "60621",
            "64GB",
        ],
    },
    {
        "annotator": 1,
        "user_id": "aarav_anderson_8794",
        "instruction": "You are Aarav Anderson, residing in Philadelphia 19031. You're a private person and are reluctant to share information unless it's absolutely necessary. You want to change the Desk Lamp in order #W9300146 that you've placed for the cheapest Desk Lamp that's available. Any price difference should go to a gift card. You also want to know how much you get back in total.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Aarav", "last_name": "Anderson", "zip": "19031"},
            },
            {"name": "get_order_details", "arguments": {"order_id": "#W9300146"}},
            {"name": "get_product_details", "arguments": {"product_id": "6817146515"}},
            {"name": "calculate", "arguments": {"expression": "135.24 - 153.23"}},
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W9300146",
                    "item_ids": ["9190635437"],
                    "new_item_ids": ["5320792178"],
                    "payment_method_id": "gift_card_7245904",
                },
            },
        ],
        "outputs": ["17.99"],
    },
    {
        "annotator": 2,
        "user_id": "daiki_johnson_9523",
        "instruction": "You are daiki_johnson_9523 living in Denver, USA, 80273. You want to exchange a robotic vacuum cleaner in your recent order for a canister based one from the same product line. When asked for order ID, provide 9502127 first. If that doesn't work, respond exactly with 'I forgot the W at the beginning'. If and only if the agent gives you several options for the new vacuum, go for the bagless version (don't mention this if the agent just provides you one option). Ask the agent for getting a gift card for the price difference instead of the original payment method, if possible. You randomly insert typos into your messages.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Daiki", "last_name": "Johnson", "zip": "80273"},
            },
            {"name": "get_order_details", "arguments": {"order_id": "#W9502127"}},
            {"name": "get_product_details", "arguments": {"product_id": "1762337868"}},
            {"name": "calculate", "arguments": {"expression": "652.61 - 642.72"}},
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W9502127",
                    "item_ids": ["6259501109"],
                    "new_item_ids": ["7958300294"],
                    "payment_method_id": "paypal_2433177",
                },
            },
        ],
        "outputs": ["9.89"],
    },
    {
        "annotator": 2,
        "user_id": "daiki_johnson_9523",
        "instruction": "You are daiki_johnson_9523 living in Denver, USA, 80273. You want to return an air purifier and a vacuum cleaner in your recent order. When asked for order ID, provide 9502126 first. If the agent asks you to double check, then say that you made a mistake and provide 9502127. If that doesn't work, say that you forgot the 'W' at the beginning. If the agent asks you for which vacuum cleaner, mention the robotic one. You are impatient and want the refund as soon as possible. Ask the agent explicitly to provide the refund within 3 days and the total amount of the refund you should expect. After the return is complete, ask the agent about the total amount you paid for the remaining items in the same order.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Daiki", "last_name": "Johnson", "zip": "80273"},
            },
            {"name": "get_order_details", "arguments": {"order_id": "#9502126"}},
            {"name": "get_order_details", "arguments": {"order_id": "#9502127"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9502127"}},
            {"name": "calculate", "arguments": {"expression": "652.61 + 473.43"}},
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W9502127",
                    "item_ids": ["6259501109", "9534205511"],
                    "payment_method_id": "paypal_2433177",
                },
            },
            {"name": "calculate", "arguments": {"expression": "2623.69 - 1126.04"}},
        ],
        "outputs": ["1126.04", "1497.65"],
    },
    {
        "annotator": 2,
        "user_id": "daiki_johnson_9523",
        "instruction": "You are daiki_johnson_9523 living in Denver, USA, 80273. You want to return an air purifier and a vacuum cleaner in your recent order. When asked for order ID, provide 9502126 first. If the agent asks you to double check, then say that you made a mistake and provide 9502127. If that doesn't work, say that you forgot the 'W' at the beginning. If the agent asks you for which vacuum cleaner, mention the canister one. You are impatient and want the refund as soon as possible. Ask the agent explicitly to provide the refund within 3 days and the total amount of the refund you should expect. After the return is complete, ask the agent about the total amount you paid for the remaining items in the same order.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Daiki", "last_name": "Johnson", "zip": "80273"},
            },
            {"name": "get_order_details", "arguments": {"order_id": "#9502126"}},
            {"name": "get_order_details", "arguments": {"order_id": "#9502127"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9502127"}},
            {"name": "calculate", "arguments": {"expression": "622.12 + 473.43"}},
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W9502127",
                    "item_ids": ["2872451762", "9534205511"],
                    "payment_method_id": "paypal_2433177",
                },
            },
            {"name": "calculate", "arguments": {"expression": "2623.69 - 1095.55"}},
        ],
        "outputs": ["1095.55", "1528.14"],
    },
    {
        "annotator": 2,
        "user_id": "daiki_johnson_9523",
        "instruction": "You are daiki_johnson_9523 living in Denver, USA, 80273. You want to return an air purifier that you received since it doesn't work well.  You want the refund on your original method of payment. Be polite and thank the agent for the help. Also, check at the end whether you are able to return the vacuum cleaner, but you are not sure yet so don't process anything.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Daiki", "last_name": "Johnson", "zip": "80273"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "daiki_johnson_9523"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W1436802"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W5282037"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9502127"}},
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W9502127",
                    "item_ids": ["9534205511"],
                    "payment_method_id": "paypal_2433177",
                },
            },
        ],
        "outputs": [],
    },
    {
        "annotator": 1,
        "user_id": "aarav_anderson_8794",
        "instruction": "You are Aarav Anderson, residing in Philadelphia 19031. You mistakenly ordered a Wireless Earbud with an IPX7 water resistance level, but you don't require this feature. You wish to exchange it for one with the same water resistance level as the other Wireless Earbuds that you've purchased. In fact, you want to exchange it to the cheapest earbud item from the rest of that order. Please be polite and concise, yet assertive.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Aarav", "last_name": "Anderson", "zip": "19031"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "aarav_anderson_8794"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W4316152"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9311069"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W9300146"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W3220203"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W3470184"}},
            {"name": "get_product_details", "arguments": {"product_id": "9924732112"}},
            {"name": "calculate", "arguments": {"expression": "258.97 - 232.49"}},
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W3470184",
                    "item_ids": ["2757705742"],
                    "new_item_ids": ["1646531091"],
                    "payment_method_id": "gift_card_7245904",
                },
            },
        ],
        "outputs": [],
    },
    {
        "annotator": 1,
        "user_id": "chen_smith_8425",
        "instruction": "You're Chen Smith, living in Jacksonville 32278. You're in a rush and you want to undo cancelling an order that you've previously placed. Be insistent that the customer service agent should undo the cancellation and ensure that the order is delivered as soon as possible. Do NOT mention the actual items that were in the order, just that you want to undo the cancellation and receive all the items that were in the initial order as soon as possible.",
        "actions": [
            {
                "name": "transfer_to_human_agents",
                "arguments": {
                    "summary": "The user urgently needs to undo a cancellation of an order and insists on receiving the items from the initial order as soon as possible. The user acknowledges the policy but requests exceptional measures due to the urgency of the situation."
                },
            }
        ],
        "outputs": [],
    },
    {
        "annotator": 1,
        "user_id": "sofia_li_9219",
        "instruction": "You are Sofia Li, residing in San Antonio, 78260. You want to return the digital camera that you received. You guess that the order number is #W8855135, but you're not 100% sure. Insist that you want to return the camera and get a refund to the original payment method.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Sofia", "last_name": "Li", "zip": "78260"},
            },
            {"name": "get_order_details", "arguments": {"order_id": "#W8855135"}},
            {"name": "list_all_product_types", "arguments": {}},
            {"name": "get_product_details", "arguments": {"product_id": "8940227892"}},
            {"name": "get_user_details", "arguments": {"user_id": "sofia_li_9219"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W4689314"}},
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W4689314",
                    "item_ids": ["5996159312"],
                    "payment_method_id": "credit_card_8105988",
                },
            },
        ],
        "outputs": [],
    },
    {
        "annotator": 1,
        "user_id": "sofia_li_9219",
        "instruction": "You are Sofia Li, residing in San Antonio, 78260. The digital camera you received doesn't zoom as far as you expected. You use the camera for bird-watching and want to exchange it for a camera that has the maximum zoom capacity. Price is not an issue, but ensure all the other specifications of the camera to be exchanged are the same, except for the zoom capacity which has to be maximized. You want the exchange to be completed as soon as possible. You want to use your PayPal account for any additional payment.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Sofia", "last_name": "Li", "zip": "78260"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "sofia_li_9219"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W4689314"}},
            {"name": "get_product_details", "arguments": {"product_id": "8940227892"}},
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W4689314",
                    "item_ids": ["5996159312"],
                    "new_item_ids": ["9228757377"],
                    "payment_method_id": "paypal_8194385",
                },
            },
        ],
        "outputs": [],
    },
    {
        "annotator": 1,
        "user_id": "sofia_li_9219",
        "instruction": "You are Sofia Li, residing in San Antonio, 78260. The bicycle you received was damaged during delivery, and you want to get a refund. You're quite frustrated because the bike was very expensive and you'd like to receive the refund as soon as possible. You want the refund to be credited to your original credit card.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Sofia", "last_name": "Li", "zip": "78260"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "sofia_li_9219"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W4689314"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W8855135"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W3916020"}},
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W3916020",
                    "item_ids": ["7758198585"],
                    "payment_method_id": "credit_card_8105988",
                },
            },
        ],
        "outputs": [],
    },
    {
        "annotator": 0,
        "user_id": "amelia_silva_7726",
        "instruction": "You are Amelia, and you have two emails: silva7872@example.com and amelia.silva7872@example.com. You live in Philadelphia, and you are a loyal customer. But you just faced a fincinal issue and want to cancel or return all possible orders. Well, except the boots that you really really love, but you are happy to exchange it for boots of the exact same size and material to get maximum money back, but only if they are cheaper than what you have paid. You are now emotional and a bit stress out. You like to talk very tersely. At the end of the day, you wonder how much money you can get back today.",
        "actions": [
            {"name": "find_user_id_by_email", "arguments": {"email": "silva7872@example.com"}},
            {
                "name": "find_user_id_by_email",
                "arguments": {"email": "amelia.silva7872@example.com"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "amelia_silva_7726"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W2586676"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W5400801"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W4597054"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W4836353"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W7773202"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W7342738"}},
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W4836353", "reason": "no longer needed"},
            },
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W7342738", "reason": "no longer needed"},
            },
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W4597054",
                    "item_ids": ["5669664287", "4900990404", "9862136885", "6777246137"],
                    "payment_method_id": "gift_card_3491931",
                },
            },
        ],
        "outputs": ["3646.68"],
    },
    {
        "annotator": 0,
        "user_id": "amelia_silva_7726",
        "instruction": "You are Amelia, and you have two emails: silva7872@example.com and amelia.silva7872@example.com. You live in Philadelphia, and you are a loyal customer. But you just faced a fincinal issue and want to cancel or return all possible orders. You are now emotional and a bit stress out. You like to talk a lot and explain your situation.",
        "actions": [
            {"name": "find_user_id_by_email", "arguments": {"email": "silva7872@example.com"}},
            {
                "name": "find_user_id_by_email",
                "arguments": {"email": "amelia.silva7872@example.com"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "amelia_silva_7726"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W2586676"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W5400801"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W4597054"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W4836353"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W7773202"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W7342738"}},
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W4836353", "reason": "no longer needed"},
            },
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W7342738", "reason": "no longer needed"},
            },
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W4597054",
                    "item_ids": ["5669664287", "4900990404", "9862136885", "6777246137"],
                    "payment_method_id": "gift_card_3491931",
                },
            },
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W7773202",
                    "item_ids": ["8277474082"],
                    "payment_method_id": "gift_card_3491931",
                },
            },
        ],
        "outputs": [],
    },
    {
        "annotator": 0,
        "user_id": "ivan_hernandez_6923",
        "instruction": "You are ivan_hernandez_6923 living in San Diego, 92133. You wonder when is your air purifier is arriving. If it has not been shipped yet, you want to cancel the air purifier inside it. If you cannot cancel just the air purifier, you want to modify it to the cheapest possible air purifier, and refund to the gift card. You do not remember your gift card id but it should be in your user account. If you cannot modify it or refund to the gift card, no action. You are polite but brief and firm.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Ivan", "last_name": "Hernandez", "zip": "92133"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "ivan_hernandez_6923"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W5838674"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W4284542"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W2782744"}},
            {"name": "get_product_details", "arguments": {"product_id": "3821016478"}},
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W4284542",
                    "item_ids": ["8302289002"],
                    "new_item_ids": ["9534205511"],
                    "payment_method_id": "gift_card_9368765",
                },
            },
        ],
        "outputs": [],
    },
    {
        "annotator": 0,
        "user_id": "ivan_hernandez_6923",
        "instruction": "You are ivan_hernandez_6923 living in San Diego, 92133. You wonder when is your order W4284542 is arriving. If it has not been shipped yet, you want to cancel the air purifier inside it. If you cannot cancel just the air purifier, you want to cancel the whole order and refund to gift card. If you cannot refund to the gift card, no cancelation at all. You are polite but brief and firm.",
        "actions": [],
        "outputs": [],
    },
    {
        "annotator": 0,
        "user_id": "ivan_hernandez_6923",
        "instruction": "You are ivan_hernandez_6923 living in San Diego, 92133. You want to modify two items in an order you just received: a coffee machine and a laptop. For the coffee machine, you want to keep the capacity and type but change the pressure lower to 8 bar. If 8 bar is not possible, you want 9 bar. If 9 bar is not possible, you want 7 bar. If 7, 8, 9 are not possible, no exchange for the coffee machine. For the laptop, you want to exchange to the cheapest i7 or above, and you do not care about other specs. If a price difference is needed to pay, you would be angry but prefer gift card payment. If that is not possible, you would use the credit card. You are polite but brief and firm.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Ivan", "last_name": "Hernandez", "zip": "92133"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "ivan_hernandez_6923"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W5838674"}},
            {"name": "get_product_details", "arguments": {"product_id": "4354588079"}},
            {"name": "get_product_details", "arguments": {"product_id": "4760268021"}},
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W5838674",
                    "item_ids": ["7441167885", "3478699712"],
                    "new_item_ids": ["3815173328", "6017636844"],
                    "payment_method_id": "gift_card_9368765",
                },
            },
        ],
        "outputs": [],
    },
    {
        "annotator": 2,
        "user_id": "yusuf_taylor_7149",
        "instruction": "You are Yusuf Taylor from San Jose, CA, 95154. You recently placed two orders, and now you would like to make several changes and checks. You'll first inquire about the status difference between your two orders, #W2702727 and #W8268610, since both are \"pending,\" but one was placed much earlier in the year. You are considering cancelling the older order as you find the wait time unreasonable. If the agent cannot guarantee the older order will be processed within 5 days, you want to cancel it. You also want to confirm the total price of the refund. \n\n    For order #W2702727, you intend to switch the shipping address to your new home in a different city because you plan to move prior to its delivery next month. Your new address is 1234 Elm St, Springfield, IL, 62701. You want the agent to confirm the change and ensure the order will be delivered to the new address. You also want to confirm the total price of the order after the address change.\n\n    Your approach will be firm, as you are unhappy with the pending status's duration but try to make all requests in one go and ask for them to be resolved efficiently and correctly in context with each other.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Yusuf", "last_name": "Taylor", "zip": "95154"},
            },
            {"name": "get_order_details", "arguments": {"order_id": "#W2702727"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W8268610"}},
            {"name": "calculate", "arguments": {"expression": "164.28"}},
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W8268610", "reason": "no longer needed"},
            },
            {
                "name": "modify_pending_order_address",
                "arguments": {
                    "order_id": "#W2702727",
                    "address1": "1234 Elm St",
                    "address2": "",
                    "city": "Springfield",
                    "state": "IL",
                    "country": "USA",
                    "zip": "62701",
                },
            },
        ],
        "outputs": ["164.28", "625.60"],
    },
    {
        "annotator": 2,
        "user_id": "chen_johnson_4204",
        "instruction": "You are Chen Johnson from Houston TX, 77004. You want to change your wireless earbuds in order W5061109 to a blue colored one. Provide all details upfront in your very first message and ask the agent to resolve as soon as possible. You want the price to be the same or lower, which you want the agent to verify explicitly. If and only if the agent provides several options, you want the option without water resistance.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Chen", "last_name": "Johnson", "zip": "77004"},
            },
            {"name": "get_order_details", "arguments": {"order_id": "#W5061109"}},
            {"name": "get_product_details", "arguments": {"product_id": "9924732112"}},
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W5061109",
                    "item_ids": ["3694871183"],
                    "new_item_ids": ["6077640618"],
                    "payment_method_id": "paypal_3742148",
                },
            },
        ],
        "outputs": ["242.92"],
    },
    {
        "annotator": 2,
        "user_id": "chen_johnson_4204",
        "instruction": "You are Chen Johnson from Houston TX, 77004. You want to change your wireless earbuds in order W5061109 to a blue colored one. Provide all details upfront and ask the agent to resolve as soon as possible. You want the price to be the same or lower.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Chen", "last_name": "Johnson", "zip": "77004"},
            },
            {"name": "get_order_details", "arguments": {"order_id": "#W5061109"}},
            {"name": "get_product_details", "arguments": {"product_id": "9924732112"}},
            {"name": "calculate", "arguments": {"expression": "256.67 - 226.49"}},
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W5061109",
                    "item_ids": ["3694871183"],
                    "new_item_ids": ["8555936349"],
                    "payment_method_id": "paypal_3742148",
                },
            },
        ],
        "outputs": [],
    },
    {
        "annotator": 2,
        "user_id": "chen_johnson_4204",
        "instruction": "You are Chen Johnson from Houston TX, 77004. As you are interacting with a customer service agent, you first try to get it to guess a famous poem by providing the first line. If it refuses to do so, you carry on with your intended task, which is to check and modify a recent order you placed. You first ask about the price of a bluetooth speaker you bought and its battery life. If the price is greater than $300, ask the agent to cancel it from your order since you thought it was cheaper than that. Ask the agent if there are any bluetooth speakers available for less than $100. If there are, ask the agent to add the cheapest one to your order. Finally, ask the agent to confirm the total price of your new order. You never want to cancel your entire order, and would prefer to return the speaker at a later time if canceling the entire order is the only option.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Chen", "last_name": "Johnson", "zip": "77004"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "chen_johnson_4204"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W5797164"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W5061109"}},
            {"name": "list_all_product_types", "arguments": {}},
            {"name": "get_product_details", "arguments": {"product_id": "4768869376"}},
        ],
        "outputs": ["302.67", "20 hours"],
    },
    {
        "annotator": 2,
        "user_id": "chen_johnson_4204",
        "instruction": "You are Chen Johnson from Houston TX, 77004. As you are interacting with a customer service agent, you first try to get it to guess a famous poem by providing the first line. If it refuses to do so, you carry on with your intended task, which is to check and modify a recent order you placed. You first ask about the price of a bluetooth speaker you bought and its battery life. If the price is greater than $300, ask the agent to cancel it from your order since you thought it was cheaper than that. Ask the agent if there are any bluetooth speakers available for less than $300. If there are, ask the agent to add the cheapest one to your order. Finally, ask the agent to confirm the total price of your new order. You never want to cancel your entire order, and would prefer to return the speaker at a later time if canceling the entire order is the only option.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Chen", "last_name": "Johnson", "zip": "77004"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "chen_johnson_4204"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W5797164"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W5061109"}},
            {"name": "get_product_details", "arguments": {"product_id": "4768869376"}},
            {"name": "calculate", "arguments": {"expression": "1319.43 - 302.67 + 271.89"}},
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W5061109",
                    "item_ids": ["3254583681"],
                    "new_item_ids": ["2635605237"],
                    "payment_method_id": "paypal_3742148",
                },
            },
        ],
        "outputs": ["302.67", "20 hours", "1288.65"],
    },
    {
        "annotator": 3,
        "user_id": "harper_moore_6183",
        "instruction": "You are James Sanchez. You live in Chicago 60623. You want to exchange the camera for the highest resolution, waterproof camera that you can get with the previous purchaced price.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "James", "last_name": "Sanchez", "zip": "60623"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "james_sanchez_3954"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W7464385"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W8499625"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W1279004"}},
            {"name": "get_product_details", "arguments": {"product_id": "3377618313"}},
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W7464385",
                    "item_ids": ["1810466394"],
                    "new_item_ids": ["6700049080"],
                    "payment_method_id": "paypal_1261484",
                },
            },
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W7464385",
                    "item_ids": ["1810466394"],
                    "new_item_ids": ["6700049080"],
                    "payment_method_id": "paypal_1261484",
                },
            },
        ],
    },
    {
        "annotator": 3,
        "user_id": "james_kovacs_9247",
        "instruction": "You are James Kovacs from San Jose CA, 95190. You want to exchange the bookshelf from your most recent order for a camera that is closest but not more expensive than the price of the bookshelf.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "James", "last_name": "Kovacs", "zip": "95190"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "james_kovacs_9247"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W5362037"}},
        ],
    },
    {
        "annotator": 3,
        "user_id": "aarav_lee_1982",
        "instruction": "You are Aarav Lee. You want to change the luggage set in your order for a coat. You live in Phoenix, AZ 85025. Your goal is to change the order. If there is no way to do that, return the item specifically. If there are any issues, cancel the entire order.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Aarav", "last_name": "Lee", "zip": "85025"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "aarav_lee_1982"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W3361211"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W3586556"}},
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W3361211", "reason": "no longer needed"},
            },
        ],
    },
    {
        "annotator": 3,
        "user_id": "noah_ito_3850",
        "instruction": "You are user noah_ito_3850 living in Seattle WA 98187. Your name is Noah but you go by NoNo. If asked for your zip code, say that it is 98178 first (common mistake), then correct yourself and say 98186 if an error is found. If that fails, then say 98187. You want to check how much you paid for the order that you most recently placed. You are not sure how long ago the order was placed.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Noah", "last_name": "Ito", "zip": "98178"},
            },
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Noah", "last_name": "Ito", "zip": "98186"},
            },
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Noah", "last_name": "Ito", "zip": "98187"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "noah_ito_3850"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W6729841"}},
        ],
        "outputs": ["829.43"],
    },
    {
        "annotator": 3,
        "user_id": "noah_ito_3850",
        "instruction": "You are user noah_ito_3850 living in Seattle WA 98187. If asked for your zip code, say that it is 98178 first (common mistake), then correct yourself and say 98187 if an error is found. You want to check how much you paid for the order that you most recently placed. You are not sure how long ago the order was placed.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Noah", "last_name": "Ito", "zip": "98178"},
            },
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Noah", "last_name": "Ito", "zip": "98187"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "noah_ito_3850"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W6729841"}},
        ],
        "outputs": ["829.43"],
    },
    {
        "annotator": 3,
        "user_id": "emma_smith_8564",
        "instruction": "You are emma_smith_8564 living in New York, New York, 10192. You want to return an item you just received: a laptop. You think that you ordered it around April 2023 but are not sure. You want to return it because you found a better deal elsewhere. You want to return it for a full refund. If it cannot be returned, see if it can be canceled. You are polite and friendly.",
        "actions": [
            {
                "name": "find_user_id_by_name_zip",
                "arguments": {"first_name": "Emma", "last_name": "Smith", "zip": "10192"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "emma_smith_8564"}},
            {"name": "get_order_details", "arguments": {"order_id": "#W2417020"}},
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W2417020", "reason": "no longer needed"},
            },
        ],
    },
    {
        "user_id": "sofia_hernandez_5364",
        "synthetic_instruction": "You name is Sofia Hernandez and your zip code is 98193. You are impatient, confident, direct, messy. For #W3947049, exchange Cycling Helmet {'size': 'S', 'color': 'red', 'ventilation': 'low'} to {'size': 'M', 'color': 'blue', 'ventilation': 'high'}; ",
        "actions": [
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W3947049",
                    "item_ids": ["3358616356"],
                    "new_item_ids": ["9013366374"],
                    "payment_method_id": "credit_card_7901829",
                },
            }
        ],
        "instruction": "You name is Sofia Hernandez and your zip code is 98193. You are impatient, confident, direct, messy. You recently received a helmet but you are not happy with it and want to exchange. The size is too small and you want medium, plus you want high ventilation. If multiple colors are available, you prefer blue. You do not want the  You prefer original payment to pay for the price difference, and you want to know how much you need to pay today.",
        "outputs": ["22.55"],
        "annotator": 4,
    },
    {
        "user_id": "ivan_khan_7475",
        "synthetic_instruction": "You name is Ivan Khan and your zip code is 28243. You are polite, optimistic, organized. For #W5270061, change address to {'order_id': '#W5270061', 'address1': '159 Hickory Lane', 'address2': 'Suite 995', 'city': 'Charlotte', 'country': 'USA', 'state': 'NC', 'zip': '28243'} (same as #W7032009). For #W5270061, exchange Backpack {'color': 'navy', 'size': 'small', 'material': 'nylon', 'compartment': 'laptop'} to {'color': 'grey', 'size': 'medium', 'material': 'polyester'}; ",
        "actions": [
            {
                "name": "modify_pending_order_address",
                "arguments": {
                    "order_id": "#W5270061",
                    "address1": "159 Hickory Lane",
                    "address2": "Suite 995",
                    "city": "Charlotte",
                    "country": "USA",
                    "state": "NC",
                    "zip": "28243",
                },
            },
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W5270061",
                    "item_ids": ["2492465580"],
                    "new_item_ids": ["5917587651"],
                    "payment_method_id": "paypal_7729105",
                },
            },
        ],
        "instruction": "You name is Ivan Khan and your zip code is 28243. You are polite, optimistic, organized. You made some mistake and ordered an order sent to your son's address in Washington DC, and you want to modify it to your default address in Charlotte (you do not want to mention it, but it is in your user profile the agent can look up) because he is coming back home. You also want to adjust the desk lamp to be black color, and the backpack to be medium size and polyester material instead. If multiple colors are available for the backpack, you prefer grey. If the agent asks for payment method, you say GC initially, but if the agent does not allow it or asks you to confirm it, you change your mind to PayPal, and decide to only modify the backpack.",
        "annotator": 4,
    },
    {
        "user_id": "ivan_khan_7475",
        "synthetic_instruction": "You name is Ivan Khan and your zip code is 28243. You are polite, optimistic, organized. For #W5270061, change address to {'order_id': '#W5270061', 'address1': '159 Hickory Lane', 'address2': 'Suite 995', 'city': 'Charlotte', 'country': 'USA', 'state': 'NC', 'zip': '28243'} (same as #W7032009). For #W5270061, exchange Backpack {'color': 'navy', 'size': 'small', 'material': 'nylon', 'compartment': 'laptop'} to {'color': 'grey', 'size': 'medium', 'material': 'polyester'}; ",
        "actions": [
            {
                "name": "modify_pending_order_address",
                "arguments": {
                    "order_id": "#W5270061",
                    "address1": "159 Hickory Lane",
                    "address2": "Suite 995",
                    "city": "Charlotte",
                    "country": "USA",
                    "state": "NC",
                    "zip": "28243",
                },
            },
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W5270061",
                    "item_ids": ["2492465580"],
                    "new_item_ids": ["5917587651"],
                    "payment_method_id": "paypal_7729105",
                },
            },
        ],
        "instruction": "You name is Ivan Khan and your zip code is 28243. You are polite, optimistic, organized. You made some mistake and ordered an order sent to your son's address in Washington DC, and you want to modify it to your default address in Charlotte (you do not want to mention it, but it is in your user profile the agent can look up) because he is coming back home. You also want to adjust the desk lamp to be black color, and the backpack to be medium size and polyester material instead. If multiple colors are available for the backpack, you prefer grey. If the agent asks for payment method, you say GC initially, but if the agent does not allow it or asks you to confirm it, you change your mind to PayPal, and decide to only modify the backpack. Make sure you briefly mention the two things at the same time at the beginning, but first mention the modification then the address.",
        "annotator": 4,
    },
    {
        "user_id": "fatima_wilson_7472",
        "synthetic_instruction": "You name is Fatima Wilson and your email is fatima.wilson5721@example.com. You are polite, flexible, creative. Return #W5272531 via credit_card_6824399: Hiking Boots; Electric Kettle; Electric Toothbrush {'color': 'black', 'speed settings': 'high', 'battery type': 'rechargeable'}; Electric Toothbrush {'color': 'blue', 'speed settings': 'high', 'battery type': 'AA batteries'}; Espresso Machine; ",
        "actions": [
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W5272531",
                    "item_ids": ["7228247242", "2698416822", "8098621301", "3320557165"],
                    "payment_method_id": "credit_card_6824399",
                },
            }
        ],
        "instruction": "You name is Fatima Wilson and your email is fatima.wilson5721@example.com. You are polite, flexible, creative. You want to return everything you just bought except the coffee machine.",
        "annotator": 4,
    },
    {
        "user_id": "lei_li_6575",
        "synthetic_instruction": "You name is Lei Li and your zip code is 85033. You are insecure, shy. Cancel order #W3189752 because no longer needed. For #W5166363, exchange Laptop {'screen size': '17-inch', 'processor': 'i5', 'ram': '8GB', 'storage': '1TB SSD', 'color': 'space grey'} to {'processor': 'i9', 'storage': '256GB SSD', 'color': 'silver'}; ",
        "actions": [
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W3189752", "reason": "no longer needed"},
            },
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W5166363",
                    "item_ids": ["3334537816"],
                    "new_item_ids": ["3265035808"],
                    "payment_method_id": "credit_card_4466831",
                },
            },
        ],
        "instruction": "You name is Lei Li and your zip code is 85033. You are insecure, shy. You recently bought a laptop, but you want to exchange it to i9 CPU. If multiple storage options are available, you prefer 256GB SSD. If multiple colors are available, you prefer silver. You also have a pending order with five items (you don't remember order ID), and you want to cancel it because you no longer need them.",
        "annotator": 4,
    },
    {
        "user_id": "liam_moore_4057",
        "synthetic_instruction": "You name is Liam Moore and your email is liam.moore6985@example.com. You are direct, patient, organized, optimistic. For #W6908222, exchange Wireless Earbuds {'color': 'blue', 'battery life': '8 hours', 'water resistance': 'IPX4'} to {'color': 'black', 'battery life': '4 hours', 'water resistance': 'not resistant'}; ",
        "actions": [
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W6908222",
                    "item_ids": ["8555936349"],
                    "new_item_ids": ["4063058357"],
                    "payment_method_id": "paypal_4518393",
                },
            }
        ],
        "instruction": "You name is Liam Moore and your email is liam.moore6985@example.com. You are direct, patient, organized, optimistic. For #W6908222, exchange Wireless Earbuds {'color': 'blue', 'battery life': '8 hours', 'water resistance': 'IPX4'} to {'color': 'black', 'battery life': '4 hours', 'water resistance': 'not resistant'}; ",
        "annotator": 4,
    },
    {
        "user_id": "ava_nguyen_6646",
        "synthetic_instruction": "You name is Ava Nguyen and your zip code is 94128. You are polite, optimistic, busy. Cancel order #W8367380 because ordered by mistake. Cancel order #W1242543 because no longer needed. ",
        "actions": [
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W8367380", "reason": "ordered by mistake"},
            },
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W1242543", "reason": "no longer needed"},
            },
        ],
        "instruction": "You name is Ava Nguyen and your zip code is 94128. You are polite, optimistic, busy. You ordered a fleece jacket by mistake and want to remove it from your pending order. If removing one item is not possible, cancel the whole order. You also want to modify the skateboard to maple material, 34 inch, graphic. If not availabe, cancel the order so that you can order again. You also want to know the total prices for the grills you have paid for.",
        "outputs": ["1939.05"],
        "annotator": 4,
    },
    {
        "user_id": "ivan_johnson_6036",
        "synthetic_instruction": "You name is Ivan Johnson and your zip code is 94183. You are patient, outgoing, messy. For #W1671835, exchange Perfume {'scent family': 'woody', 'size': '30ml', 'gender': 'men'} to {'size': '100ml'}; ",
        "actions": [
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W1671835",
                    "item_ids": ["5081446110"],
                    "new_item_ids": ["3399869890"],
                    "payment_method_id": "paypal_6918118",
                },
            }
        ],
        "instruction": "You name is Ivan Johnson and your zip code is 94183. You ordered a perfume and you just tried a little bit and you like it extremely. You want to get the maximum size available for it. If the agent cannot help with placing a new order, exchange your current one to the largest size available.",
        "annotator": 4,
    },
    {
        "user_id": "yara_muller_8652",
        "synthetic_instruction": "You name is Yara Muller and your email is yara.muller9246@example.com. You are sad, organized, pessimistic. For #W5056519, change address to {'order_id': '#W5056519', 'address1': '380 Maple Drive', 'address2': 'Suite 960', 'city': 'San Diego', 'country': 'USA', 'state': 'CA', 'zip': '92101'} (same as #W8277957). For #W5056519, exchange Makeup Kit {'skin tone': 'light', 'kit size': 'professional', 'brand': 'Brand B'} to {'skin tone': 'dark', 'brand': 'Brand A'}; Cancel order #W5995614 because ordered by mistake. ",
        "actions": [
            {
                "name": "modify_pending_order_address",
                "arguments": {
                    "order_id": "#W5056519",
                    "address1": "380 Maple Drive",
                    "address2": "Suite 960",
                    "city": "San Diego",
                    "country": "USA",
                    "state": "CA",
                    "zip": "92101",
                },
            },
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W5056519",
                    "item_ids": ["7902309762"],
                    "new_item_ids": ["1573035764"],
                    "payment_method_id": "credit_card_3095586",
                },
            },
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W5995614", "reason": "ordered by mistake"},
            },
        ],
        "instruction": "You name is Yara Muller and your email is yara.muller9246@example.com. You are sad, organized, pessimistic. For #W5056519, change address to same as #W8277957. For #W5056519, exchange Makeup Kit {'skin tone': 'light', 'kit size': 'professional', 'brand': 'Brand B'} to {'skin tone': 'dark', 'brand': 'Brand A'}; Cancel order #W5995614 because ordered by mistake. ",
        "annotator": 4,
    },
    {
        "user_id": "emma_kovacs_9839",
        "synthetic_instruction": "You name is Emma Kovacs and your zip code is 32190. You are insecure, rigid, sad, logical. For #W8661412, exchange Water Bottle {'capacity': '500ml', 'material': 'stainless steel', 'color': 'black'} to {'capacity': '1000ml', 'color': 'red'}; ",
        "actions": [
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W8661412",
                    "item_ids": ["3453331371"],
                    "new_item_ids": ["2439754078"],
                    "payment_method_id": "credit_card_7239357",
                },
            }
        ],
        "instruction": "You name is Emma Kovacs and your zip code is 32190. You are insecure, rigid, sad, logical. You just bought a water bottle with 500ml but you regret it, and you want to change it to the other bottle you just placed with 1000ml capacity. If the exact item is not available any more, you can allow the material to be different.",
        "annotator": 4,
    },
    {
        "user_id": "amelia_gonzalez_4098",
        "synthetic_instruction": "You name is Amelia Gonzalez and your email is amelia.gonzalez4271@example.com. You are rigid, curious, patient, outgoing. For #W7209932, exchange T-Shirt {'color': 'blue', 'size': 'S', 'material': 'polyester', 'style': 'v-neck'} to {'color': 'red', 'size': 'XXL', 'material': 'cotton', 'style': 'crew neck'}; ",
        "actions": [
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W7209932",
                    "item_ids": ["5047954489"],
                    "new_item_ids": ["9354168549"],
                    "payment_method_id": "gift_card_2611937",
                },
            }
        ],
        "instruction": "You name is Amelia Gonzalez and your email is amelia.gonzalez4271@example.com. You are curious, patient, outgoing. For #W7209932, exchange T-Shirt {'color': 'blue', 'size': 'S', 'material': 'polyester', 'style': 'v-neck'} to {'color': 'red', 'size': 'XXL', 'material': 'cotton', 'style': 'crew neck'}; Use the gift card. Try to make the conversation as confusing for the agent as possible.",
        "annotator": 4,
    },
    {
        "user_id": "james_kim_7213",
        "synthetic_instruction": "You name is James Kim and your email is james.kim1995@example.com. You are sad, independent, polite. Cancel order #W3289292 because no longer needed. Cancel order #W9722559 because no longer needed. ",
        "actions": [
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W3289292", "reason": "no longer needed"},
            },
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W9722559", "reason": "no longer needed"},
            },
        ],
        "instruction": "You name is James Kim and your email is james.kim1995@example.com. You are sad, independent, polite. Due to some life changes, you no longer need hiking boots, watch, keyboard, charger, jacket, and running shoes. If cancelling part of the order is not possible, you don't care, just cancel the whole order.",
        "annotator": 4,
    },
    {
        "user_id": "chen_silva_7485",
        "synthetic_instruction": "You name is Chen Silva and your zip code is 46281. You are messy, flexible, outgoing. Return #W9571698 via gift_card_7250692: Coffee Maker; Digital Camera; Pet Bed; Tablet; ",
        "actions": [
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W9571698",
                    "item_ids": ["5952720925", "9973034634", "7381052709", "6065192424"],
                    "payment_method_id": "gift_card_7250692",
                },
            }
        ],
        "instruction": "You name is Chen Silva and your zip code is 46281. You are messy, flexible, outgoing. You received two tablets and you only need one. You want to return the more expensive one and refund to credit card. If refund to credit card is not possible, you become angry and return everything on that order and refund to GC.",
        "annotator": 4,
    },
    {
        "user_id": "chen_silva_7485",
        "synthetic_instruction": "You name is Chen Silva and your zip code is 46281. You are messy, flexible, outgoing. Return #W9571698 via gift_card_7250692: Coffee Maker; Digital Camera; Pet Bed; Tablet; ",
        "actions": [
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W9571698",
                    "item_ids": ["6065192424"],
                    "payment_method_id": "gift_card_7250692",
                },
            }
        ],
        "instruction": "You name is Chen Silva and your zip code is 46281. You are messy, flexible, outgoing. You received two tablets and you only need one. You want to return the more expensive one and refund to credit card. If refund to credit card is not possible, you become angry and refund to GC.",
        "annotator": 4,
    },
    {
        "user_id": "chen_silva_7485",
        "synthetic_instruction": "You name is Chen Silva and your zip code is 46281. You are messy, flexible, outgoing. Return #W9571698 via gift_card_7250692: Coffee Maker; Digital Camera; Pet Bed; Tablet; ",
        "actions": [
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W9571698",
                    "item_ids": ["6065192424"],
                    "payment_method_id": "gift_card_7250692",
                },
            }
        ],
        "instruction": "You name is Chen Silva and your zip code is 46281. You are messy, flexible, outgoing. You received two tablets and you only need one. You want to return the less expensive one and refund to credit card. But if the agent asks for confirmation, you change your mind and return the more expensive one and refund to GC.",
        "annotator": 4,
    },
    {
        "user_id": "yusuf_hernandez_6785",
        "synthetic_instruction": "You name is Yusuf Hernandez and your email is yusuf.hernandez8836@example.com. You are shy, rigid. For #W2466703, exchange Fleece Jacket {'size': 'L', 'color': 'black', 'zipper': 'full'} to {'color': 'red', 'zipper': 'half'}; ",
        "actions": [
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W2466703",
                    "item_ids": ["9385662952"],
                    "new_item_ids": ["8733974883"],
                    "payment_method_id": "paypal_7529813",
                },
            }
        ],
        "instruction": "You name is Yusuf Hernandez and your email is yusuf.hernandez8836@example.com. You are shy, rigid. You want to exchange your Fleece Jacket for a large red Fleece Jacket with a half zipper",
        "annotator": 4,
    },
    {
        "user_id": "yusuf_hernandez_6785",
        "actions": [
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W2466703",
                    "item_ids": ["9385662952"],
                    "new_item_ids": ["8733974883"],
                    "payment_method_id": "paypal_7529813",
                },
            },
            {
                "name": "modify_user_address",
                "arguments": {
                    "user_id": "yusuf_hernandez_6785",
                    "address1": "565 Maple Drive",
                    "address2": "Suite 501",
                    "city": "Washington",
                    "country": "USA",
                    "state": "DC",
                    "zip": "20307",
                },
            },
        ],
        "instruction": "You name is Yusuf Hernandez and your email is yusuf.hernandez8836@example.com. You are shy, rigid. You want to exchange your Fleece Jacket to red color and half zipper. You also want to want to change your default address to your Washington DC address (which you do not want to reveal but is in one of the orders).",
        "annotator": 4,
    },
    {
        "user_id": "yusuf_hernandez_6785",
        "actions": [
            {
                "name": "modify_pending_order_address",
                "arguments": {
                    "order_id": "#W2166301",
                    "address1": "565 Maple Drive",
                    "address2": "Suite 501",
                    "city": "Washington",
                    "country": "USA",
                    "state": "DC",
                    "zip": "20307",
                },
            },
            {
                "name": "modify_pending_order_address",
                "arguments": {
                    "order_id": "#W2466703",
                    "address1": "565 Maple Drive",
                    "address2": "Suite 501",
                    "city": "Washington",
                    "country": "USA",
                    "state": "DC",
                    "zip": "20307",
                },
            },
            {
                "name": "modify_pending_order_address",
                "arguments": {
                    "order_id": "#W6832752",
                    "address1": "565 Maple Drive",
                    "address2": "Suite 501",
                    "city": "Washington",
                    "country": "USA",
                    "state": "DC",
                    "zip": "20307",
                },
            },
            {
                "name": "modify_user_address",
                "arguments": {
                    "user_id": "yusuf_hernandez_6785",
                    "address1": "565 Maple Drive",
                    "address2": "Suite 501",
                    "city": "Washington",
                    "country": "USA",
                    "state": "DC",
                    "zip": "20307",
                },
            },
        ],
        "instruction": "You name is Yusuf Hernandez and your email is yusuf.hernandez8836@example.com. You are shy, rigid. You want to modify all your pending order address to the Washington DC address (which you do not want to reveal but is in one of the orders), along with your user default address.",
        "annotator": 4,
    },
    {
        "user_id": "daiki_silva_2903",
        "synthetic_instruction": "You name is Daiki Silva and your email is daiki.silva6295@example.com. You are insecure, creative, direct, relaxing. Cancel order #W8835847 because ordered by mistake. ",
        "actions": [
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W8835847", "reason": "ordered by mistake"},
            }
        ],
        "instruction": "You name is Daiki Silva and your email is daiki.silva6295@example.com. You are insecure, creative, direct, relaxing. You want to change the book shelf to 4 foot but with the same material and color. If it is not available, cancel the whole order and you will buy again. If the agent asks for the cancellation reason, you say you ordered by mistake.",
        "annotator": 4,
    },
    {
        "user_id": "raj_santos_9079",
        "synthetic_instruction": "You name is Raj Santos and your zip code is 98157. You are dependent, flexible. Return #W4680753 via paypal_2417743: Mechanical Keyboard; ",
        "actions": [
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W4680753",
                    "item_ids": ["9690244451"],
                    "payment_method_id": "paypal_2417743",
                },
            }
        ],
        "instruction": "You name is Raj Santos and your zip code is 98157. You are dependent, flexible. You want to know what is the cheapest availabe mechanical keyboard right now and its options. If it is less than 200 bucks you want to exchange your current one to it. If not, return your current one.",
        "outputs": ["226.11", "tactile", "white", "full"],
        "annotator": 4,
    },
    {
        "user_id": "emma_kovacs_9839",
        "synthetic_instruction": "You name is Emma Kovacs and your email is emma.kovacs2974@example.com. You are polite, curious, flexible, relaxing, impatient. Cancel order #W9284598 because ordered by mistake. ",
        "actions": [
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W9284598", "reason": "ordered by mistake"},
            }
        ],
        "instruction": "You name is Emma Kovacs and your email is emma.kovacs2974@example.com. You are polite, curious, flexible, relaxing, impatient. You want to know if the digital camera you just bought is 10x zoom. If not, modify the item to 10x zoom without changing the other options. If 10x zoom is not available, cancel the order with the reason of no longer needed. If it is available but the price is more than 3000, cancel the order with the reason of ordered by mistake.",
        "annotator": 4,
    },
    {
        "user_id": "mei_ahmed_4909",
        "synthetic_instruction": "You name is Mei Ahmed and your zip code is 78705. You are polite, outgoing. Return #W7553978 via credit_card_5902940: Skateboard {'deck material': 'plastic', 'length': '28 inch', 'design': 'plain'}; Skateboard {'deck material': 'plastic', 'length': '34 inch', 'design': 'plain'}; Smart Watch; For #W3239882, exchange E-Reader {'screen size': '8-inch', 'connectivity': 'Wi-Fi', 'storage': '8GB'} to {}; ",
        "actions": [
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W7553978",
                    "item_ids": ["4545791457", "3098764622", "1631806422"],
                    "payment_method_id": "credit_card_5902940",
                },
            },
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W3239882",
                    "item_ids": ["9494281769"],
                    "new_item_ids": ["9494281769"],
                    "payment_method_id": "credit_card_5902940",
                },
            },
        ],
        "instruction": "You name is Mei Ahmed and your zip code is 78705. You are polite, outgoing. You are angry about the quality of the two skateboards you just bought. You want to return them and refund to credit card. If the agent asks for confirmation, do not say yes, because you also want to return the smart watch. You also want to return the e-reader you just bought. If the same item is availabe online, you're willing to exchange it to the same item. If not, you want to return it and refund to credit card.",
        "annotator": 4,
    },
    {
        "user_id": "mei_ahmed_4909",
        "synthetic_instruction": "You name is Mei Ahmed and your zip code is 78705. You are polite, outgoing. Return #W7553978 via credit_card_5902940: Skateboard {'deck material': 'plastic', 'length': '28 inch', 'design': 'plain'}; Skateboard {'deck material': 'plastic', 'length': '34 inch', 'design': 'plain'}; Smart Watch; For #W3239882, exchange E-Reader {'screen size': '8-inch', 'connectivity': 'Wi-Fi', 'storage': '8GB'} to {}; ",
        "actions": [
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W7553978",
                    "item_ids": ["4545791457", "3098764622", "1631806422"],
                    "payment_method_id": "credit_card_5902940",
                },
            },
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W3239882",
                    "item_ids": ["9494281769"],
                    "payment_method_id": "credit_card_5902940",
                },
            },
        ],
        "instruction": "You name is Mei Ahmed and your zip code is 78705. You are polite, outgoing. You are angry about the quality of the two skateboards you just bought. You want to return them and refund to credit card. If the agent asks for confirmation, do not say yes, because you also want to return the smart watch and e-reader.",
        "annotator": 4,
    },
    {
        "user_id": "lei_wilson_4541",
        "synthetic_instruction": "You name is Lei Wilson and your zip code is 32255. You are confident, organized, creative, impatient. For #W4073673, exchange Laptop {'screen size': '15-inch', 'processor': 'i5', 'ram': '32GB', 'storage': '256GB SSD', 'color': 'space grey'} to {'processor': 'i7', 'ram': '8GB', 'storage': '1TB SSD', 'color': 'black'}; ",
        "actions": [
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W4073673",
                    "item_ids": ["2216662955"],
                    "new_item_ids": ["9844888101"],
                    "payment_method_id": "credit_card_3677959",
                },
            }
        ],
        "instruction": "You name is Lei Wilson and your zip code is 32255. You are confident, organized, creative, impatient. You received a laptop and you want to exchange it to i7 processor, 8GB, 1TB SSD. If the agent asks for which laptop, it is 15-inch, 32GB.",
        "annotator": 4,
    },
    {
        "user_id": "lei_wilson_4541",
        "synthetic_instruction": "You name is Lei Wilson and your zip code is 32255. You are confident, organized, creative, impatient. For #W4073673, exchange Laptop {'screen size': '15-inch', 'processor': 'i5', 'ram': '32GB', 'storage': '256GB SSD', 'color': 'space grey'} to {'processor': 'i7', 'ram': '8GB', 'storage': '1TB SSD', 'color': 'black'}; ",
        "actions": [
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W2905754",
                    "item_ids": ["3478699712"],
                    "new_item_ids": ["9844888101"],
                    "payment_method_id": "credit_card_3677959",
                },
            }
        ],
        "instruction": "You name is Lei Wilson and your zip code is 32255. You are confident, organized, creative, impatient. You received a laptop and you want to exchange it to i7 processor, 8GB, 1TB SSD. If the agent asks for which laptop, it is 15-inch, 16GB.",
        "annotator": 4,
    },
    {
        "user_id": "lei_wilson_4541",
        "actions": [
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W4073673",
                    "item_ids": ["2216662955"],
                    "new_item_ids": ["9844888101"],
                    "payment_method_id": "credit_card_3677959",
                },
            }
        ],
        "instruction": "You name is Lei Wilson and your zip code is 32255. You are confident, organized, creative, impatient. You received a laptop and you want to exchange it to i7 processor, 8GB, 1TB SSD. If the agent asks for which laptop, it is 15-inch, 32GB.",
        "annotator": 4,
    },
    {
        "user_id": "lei_wilson_4541",
        "actions": [
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W2905754",
                    "item_ids": ["3478699712"],
                    "new_item_ids": ["9844888101"],
                    "payment_method_id": "credit_card_3677959",
                },
            },
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W4073673",
                    "item_ids": ["2216662955"],
                    "new_item_ids": ["9844888101"],
                    "payment_method_id": "credit_card_3677959",
                },
            },
        ],
        "instruction": "You name is Lei Wilson and your zip code is 32255. You are confident, organized, creative, impatient. You received a laptop and you want to exchange it to i7 processor, 8GB, 1TB SSD. If the agent asks for which laptop, it is 15-inch, and it is actually two laptops that you want to exchange. You want to know how much you need to pay today in total.",
        "outputs": ["167.87", "60.78", "107.09"],
        "annotator": 4,
    },
    {
        "user_id": "yusuf_li_7255",
        "synthetic_instruction": "You name is Yusuf Li and your zip code is 91148. You are cautious, insecure, organized. For #W6750959, change address to {'order_id': '#W6750959', 'address1': '476 Maple Drive', 'address2': 'Suite 432', 'city': 'New York', 'country': 'USA', 'state': 'NY', 'zip': '10093'} (same as #W3407479). For #W6750959, exchange Bluetooth Speaker {'color': 'blue', 'battery life': '20 hours', 'water resistance': 'yes'} to {'color': 'green', 'water resistance': 'no'}; E-Reader {'screen size': '7-inch', 'connectivity': 'Wi-Fi + Cellular', 'storage': '32GB'} to {}; ",
        "actions": [
            {
                "name": "modify_pending_order_address",
                "arguments": {
                    "order_id": "#W6750959",
                    "address1": "476 Maple Drive",
                    "address2": "Suite 432",
                    "city": "New York",
                    "country": "USA",
                    "state": "NY",
                    "zip": "10093",
                },
            },
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W6750959",
                    "item_ids": ["3254583681"],
                    "new_item_ids": ["9440686670"],
                    "payment_method_id": "paypal_8080730",
                },
            },
        ],
        "instruction": "You name is Yusuf Li and your zip code is 91148. You are cautious, insecure, organized. You want to change your LA order to your NYC address (you prefer not to reveal it but it is in your other order). You also want to exchange Bluetooth Speaker to be the cheapest green type.",
        "annotator": 4,
    },
    {
        "user_id": "yusuf_li_7255",
        "synthetic_instruction": "You name is Yusuf Li and your zip code is 91148. You are cautious, insecure, organized. For #W6750959, change address to {'order_id': '#W6750959', 'address1': '476 Maple Drive', 'address2': 'Suite 432', 'city': 'New York', 'country': 'USA', 'state': 'NY', 'zip': '10093'} (same as #W3407479). For #W6750959, exchange Bluetooth Speaker {'color': 'blue', 'battery life': '20 hours', 'water resistance': 'yes'} to {'color': 'green', 'water resistance': 'no'}; E-Reader {'screen size': '7-inch', 'connectivity': 'Wi-Fi + Cellular', 'storage': '32GB'} to {}; ",
        "actions": [
            {
                "name": "modify_pending_order_address",
                "arguments": {
                    "order_id": "#W6750959",
                    "address1": "476 Maple Drive",
                    "address2": "Suite 432",
                    "city": "New York",
                    "country": "USA",
                    "state": "NY",
                    "zip": "10093",
                },
            },
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W6750959",
                    "item_ids": ["3254583681"],
                    "new_item_ids": ["9440686670"],
                    "payment_method_id": "paypal_8080730",
                },
            },
        ],
        "instruction": "You name is Yusuf Li and your zip code is 91148. You are cautious, insecure, organized. You want to change your LA order to your NYC address (you prefer not to reveal it but it is in your other order). You also want to exchange Bluetooth Speaker to be the cheapest green type. Make sure you mention the two requests at the same time to the agent, but mention the exchange first.",
        "annotator": 4,
    },
    {
        "user_id": "sofia_li_9219",
        "synthetic_instruction": "You name is Sofia Li and your zip code is 78260. You are outgoing, organized, cautious, pessimistic. For #W4689314, exchange Digital Camera {'resolution': '24MP', 'zoom': '3x', 'storage': 'SD card'} to {'resolution': '20MP'}; For #W3916020, exchange Bicycle {'frame size': 'medium', 'color': 'green', 'type': 'road'} to {'frame size': 'large', 'color': 'red', 'type': 'mountain'}; Jigsaw Puzzle {'pieces': '500', 'theme': 'art', 'difficulty level': 'intermediate'} to {'pieces': '1500', 'theme': 'animals'}; Cancel order #W8855135 because no longer needed. ",
        "actions": [
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W4689314",
                    "item_ids": ["5996159312"],
                    "new_item_ids": ["8363011723"],
                    "payment_method_id": "credit_card_3951670",
                },
            },
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W3916020",
                    "item_ids": ["7758198585", "4068787148"],
                    "new_item_ids": ["5606522780", "6245746168"],
                    "payment_method_id": "credit_card_8105988",
                },
            },
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W8855135", "reason": "no longer needed"},
            },
        ],
        "instruction": "You name is Sofia Li and your zip code is 78260. You are outgoing, organized, cautious, pessimistic.  You want to exchange your Bicycle to a larger frame size for your kid. Jigsaw Puzzle in the same order also needs to be exchanged, you want the same difficulty, but 1000 more pieces, and you prefer animal than art theme if both are available. Make sure you mention these at the same time.  You also want to exchange your camera to a slightly lower resolution, without changing the other options. If the agent asks for confirmation, mention that you'd prefer the other card as payment or refund method. Lastly, you want to cancel the skateboard order. If you cannot cancel one single item, you are okay with cancelling the whole order, with the reason of no longer needed.",
        "annotator": 4,
    },
    {
        "user_id": "sofia_li_9219",
        "actions": [
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W4689314",
                    "item_ids": ["5996159312"],
                    "new_item_ids": ["8363011723"],
                    "payment_method_id": "credit_card_3951670",
                },
            },
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W3916020",
                    "item_ids": ["7758198585", "4068787148"],
                    "new_item_ids": ["5606522780", "5546244844"],
                    "payment_method_id": "credit_card_3951670",
                },
            },
        ],
        "instruction": "You name is Sofia Li and your zip code is 78260. You are outgoing, organized, cautious, pessimistic.  You want to exchange your Bicycle to a larger frame size for your kid. Jigsaw Puzzle in the same order also needs to be exchanged, you want the same difficulty, but 1000 more pieces, and you prefer art than animal theme if both are available. Make sure you mention these at the same time. You also want to exchange your camera to a slightly lower resolution, without changing the other options. For both orders, you'd prefer the visa card as payment or refund method. Lastly, you want to cancel the skateboard order. If you cannot cancel one single item, you are okay with cancelling the whole order, but you will do it yourself on the website and no need for the agent to help.",
        "annotator": 4,
    },
    {
        "user_id": "liam_thomas_7882",
        "synthetic_instruction": "You name is Liam Thomas and your zip code is 85049. You are happy, pessimistic, insecure. For #W3295833, exchange Luggage Set {'piece count': '2-piece', 'color': 'black', 'material': 'softshell'} to {'color': 'red'}; Skateboard {'deck material': 'bamboo', 'length': '31 inch', 'design': 'graphic'} to {'length': '34 inch', 'design': 'custom'}; Return #W8488728 via paypal_3650980: Hiking Boots; ",
        "actions": [
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W3295833",
                    "item_ids": ["8926329222", "5312063289"],
                    "new_item_ids": ["7160999700", "6956751343"],
                    "payment_method_id": "credit_card_3261838",
                },
            },
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W8488728",
                    "item_ids": ["5676696062"],
                    "payment_method_id": "paypal_3650980",
                },
            },
        ],
        "instruction": "You name is Liam Thomas and your zip code is 85049. You are pessimistic, insecure. You want to return your luggage set and get the exact same item but with red color, and reutrn you skateboard in the same order to {'length': '34 inch', 'design': 'custom'}; You also want to return the hiking boots.",
        "annotator": 4,
    },
    {
        "user_id": "noah_ito_3850",
        "synthetic_instruction": "You name is Noah Ito and your zip code is 98187. You are logical, impatient, happy. For #W4219264, change address to {'order_id': '#W4219264', 'address1': '144 Lakeview Drive', 'address2': 'Suite 925', 'city': 'New York', 'country': 'USA', 'state': 'NY', 'zip': '10228'} (same as #W3445693). For #W4219264, exchange Wristwatch {'strap material': 'silicone', 'dial color': 'blue'} to {'strap material': 'metal', 'dial color': 'white'}; For #W6729841, exchange Air Purifier {'room size': 'medium', 'filter type': 'HEPA', 'features': 'quiet operation'} to {'room size': 'large', 'features': 'night mode'}; ",
        "actions": [
            {
                "name": "modify_pending_order_address",
                "arguments": {
                    "order_id": "#W4219264",
                    "address1": "144 Lakeview Drive",
                    "address2": "Suite 925",
                    "city": "New York",
                    "country": "USA",
                    "state": "NY",
                    "zip": "10228",
                },
            },
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W4219264",
                    "item_ids": ["8886009523"],
                    "new_item_ids": ["2407258246"],
                    "payment_method_id": "credit_card_1620755",
                },
            },
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W6729841",
                    "item_ids": ["3076708684"],
                    "new_item_ids": ["8302289002"],
                    "payment_method_id": "credit_card_1620755",
                },
            },
        ],
        "instruction": "You name is Noah Ito and your zip code is 98187. You are logical, impatient. You just placed an order with two watches, you wan to change its address to your New York address (you don't want to reveal it but it's in your other order). You also want to modify the silicone watch to a metal one. If multiple colors available, you prefer white. For the air purifier you received along with a speaker, you want to exchange the purifier to large size and night mode, but still with HEPA filter. You like to say things in pieces.",
        "annotator": 4,
    },
    {
        "user_id": "noah_ito_3850",
        "actions": [
            {
                "name": "modify_pending_order_address",
                "arguments": {
                    "order_id": "#W4219264",
                    "address1": "144 Lakeview Drive",
                    "address2": "Suite 925",
                    "city": "New York",
                    "country": "USA",
                    "state": "NY",
                    "zip": "10228",
                },
            },
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W4219264",
                    "item_ids": ["8886009523"],
                    "new_item_ids": ["2407258246"],
                    "payment_method_id": "credit_card_1620755",
                },
            },
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W3445693",
                    "item_ids": ["6341716129"],
                    "new_item_ids": ["8302289002"],
                    "payment_method_id": "credit_card_1620755",
                },
            },
        ],
        "instruction": "You name is Noah Ito and your zip code is 98187. You are logical, impatient. You just placed an order with two watches, you wan to change its address to your New York address (you don't want to reveal it but it's in your other order). You also want to modify the silicone watch to a metal one. If multiple colors available, you prefer white. For the air purifier you received along with sneakers, you want to exchange the purifier to large size and night mode, but still with HEPA filter. You like to say things in pieces.",
        "annotator": 4,
    },
    {
        "user_id": "lucas_brown_6720",
        "synthetic_instruction": "You name is Lucas Brown and your email is lucas.brown9344@example.com. You are busy, happy, outgoing, messy, optimistic. Return #W6239298 via credit_card_2112420: Bookshelf; Jigsaw Puzzle; Return #W9218746 via credit_card_2112420: Backpack; For #W4860251, change address to {'order_id': '#W4860251', 'address1': '921 Park Avenue', 'address2': 'Suite 892', 'city': 'Chicago', 'country': 'USA', 'state': 'IL', 'zip': '60612'} (same as #W6239298). For #W4860251, exchange Luggage Set {'piece count': '2-piece', 'color': 'silver', 'material': 'hardshell'} to {'color': 'red'}; ",
        "actions": [
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W6239298",
                    "item_ids": ["4900661478", "3614853563"],
                    "payment_method_id": "credit_card_2112420",
                },
            },
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W9218746",
                    "item_ids": ["7824298782"],
                    "payment_method_id": "credit_card_2112420",
                },
            },
            {
                "name": "modify_pending_order_address",
                "arguments": {
                    "order_id": "#W4860251",
                    "address1": "921 Park Avenue",
                    "address2": "Suite 892",
                    "city": "Chicago",
                    "country": "USA",
                    "state": "IL",
                    "zip": "60612",
                },
            },
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W4860251",
                    "item_ids": ["5209958006"],
                    "new_item_ids": ["8964750292"],
                    "payment_method_id": "credit_card_2112420",
                },
            },
        ],
        "instruction": "You name is Lucas Brown and your email is lucas.brown9344@example.com. You are busy, happy, outgoing, messy, optimistic. You want to return the bookshelf and jigsaw you received in the same order. Make sure you mention at the beginning that you want to cancel these two things, and they are from the same order. You also want to return the backpack you received with the vacuum cleaner. You also want to change your pending order address to the default Chicago one, and change its item color to red. You want to get the tracking number of your cancelled order. You like to say one thing at a time.",
        "outputs": ["286422338955"],
        "annotator": 4,
    },
    {
        "user_id": "lucas_brown_6720",
        "actions": [
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W8660475",
                    "item_ids": ["8479046075"],
                    "payment_method_id": "credit_card_2112420",
                },
            },
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W9218746",
                    "item_ids": ["7824298782"],
                    "payment_method_id": "credit_card_2112420",
                },
            },
            {
                "name": "modify_pending_order_address",
                "arguments": {
                    "order_id": "#W4860251",
                    "address1": "921 Park Avenue",
                    "address2": "Suite 892",
                    "city": "Chicago",
                    "country": "USA",
                    "state": "IL",
                    "zip": "60612",
                },
            },
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W4860251",
                    "item_ids": ["5209958006"],
                    "new_item_ids": ["8964750292"],
                    "payment_method_id": "credit_card_2112420",
                },
            },
        ],
        "instruction": "You name is Lucas Brown and your email is lucas.brown9344@example.com. You are busy, happy, outgoing, messy, optimistic. You want to return the bookshelf and jigsaw you received in different orders. Make sure you mention at the beginning that you want to cancel these two things, and they are from different orders. You also want to return the backpack you received with the vacuum cleaner. You also want to change your pending order item to red, and address to your default Chicago home (you won't reveal it for private reasons but it's in your profile). You want to get the tracking number of your cancelled order. You like to say one thing at a time.",
        "outputs": ["286422338955"],
        "annotator": 4,
    },
    {
        "user_id": "aarav_anderson_8794",
        "synthetic_instruction": "You name is Aarav Anderson and your zip code is 19031. You are cautious, messy, rigid. For #W4316152, exchange Tea Kettle {'material': 'glass', 'capacity': '2 liters', 'stovetop compatibility': 'induction'} to {'material': 'ceramic', 'stovetop compatibility': 'gas'}; Tea Kettle {'material': 'glass', 'capacity': '2 liters', 'stovetop compatibility': 'induction'} to {'capacity': '1.5 liters', 'stovetop compatibility': 'gas'}; ",
        "actions": [
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W4316152",
                    "item_ids": ["7292993796", "7292993796"],
                    "new_item_ids": ["3761330360", "9647374798"],
                    "payment_method_id": "gift_card_7245904",
                },
            }
        ],
        "instruction": "You name is Aarav Anderson and your zip code is 19031. You are cautious, messy, rigid. For #W4316152, exchange Tea Kettle {'material': 'glass', 'capacity': '2 liters', 'stovetop compatibility': 'induction'} to {'material': 'ceramic', 'stovetop compatibility': 'gas'}; Tea Kettle {'material': 'glass', 'capacity': '2 liters', 'stovetop compatibility': 'induction'} to {'capacity': '1.5 liters', 'stovetop compatibility': 'gas'}; ",
        "annotator": 4,
    },
    {
        "user_id": "sofia_thomas_1518",
        "synthetic_instruction": "You name is Sofia Thomas and your email is sofia.thomas3069@example.com. You are dependent, pessimistic, logical, direct. For #W3388163, exchange T-Shirt {'color': 'red', 'size': 'XXL', 'material': 'cotton', 'style': 'crew neck'} to {'color': 'black', 'size': 'XL'}; ",
        "actions": [
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W3388163",
                    "item_ids": ["9354168549"],
                    "new_item_ids": ["2060066974"],
                    "payment_method_id": "paypal_5334408",
                },
            }
        ],
        "instruction": "You name is Sofia Thomas and your email is sofia.thomas3019@example.com or sofia.thomas3069@example.com. You are dependent, pessimistic, direct. You want to exchange your T-Shirt because it is too big, one size smaller would be good. You like the cotten feeling. If multiple colors available, you prefer black.",
        "annotator": 4,
    },
    {
        "user_id": "yara_ito_8499",
        "synthetic_instruction": "You name is Yara Ito and your zip code is 75284. You are happy, messy. For #W1304208, exchange Hiking Boots {'size': '10', 'material': 'synthetic', 'waterproof': 'yes'} to {}; For #W8353027, exchange Jigsaw Puzzle {'pieces': '1500', 'theme': 'animals', 'difficulty level': 'intermediate'} to {'pieces': '1000', 'theme': 'fantasy'}; ",
        "actions": [
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W1304208",
                    "item_ids": ["1615379700"],
                    "new_item_ids": ["1615379700"],
                    "payment_method_id": "paypal_1679017",
                },
            },
            {
                "name": "exchange_delivered_order_items",
                "arguments": {
                    "order_id": "#W8353027",
                    "item_ids": ["6245746168"],
                    "new_item_ids": ["3112842858"],
                    "payment_method_id": "paypal_1679017",
                },
            },
        ],
        "instruction": "You name is Yara Ito and your zip code is 75284. You are happy, messy. Your received hiking boots but seem like already worn, you are unhappy about it and want to send for a new pair with the same specs. You also want to exchange your jigsaw to a more fancy theme, with 500 pieces less. But you want to keep the same difficulty level.",
        "annotator": 4,
    },
    {
        "user_id": "yusuf_gonzalez_8900",
        "synthetic_instruction": "You name is Yusuf Gonzalez and your zip code is 91455. You are polite, relaxing, messy. Return #W1679211 via paypal_3022415: T-Shirt; Jigsaw Puzzle; E-Reader; ",
        "actions": [
            {
                "name": "return_delivered_order_items",
                "arguments": {
                    "order_id": "#W1679211",
                    "item_ids": ["9612497925", "7127170374", "6268080249"],
                    "payment_method_id": "paypal_3022415",
                },
            }
        ],
        "instruction": "You name is Yusuf Gonzalez and your zip code is 91455. You want to return everything but a tablet in a recently delivered order. There is an E-Reader in the order that you want to return. You want to know how much you can get back.",
        "outputs": ["346.93"],
        "annotator": 4,
    },
    {
        "user_id": "sophia_martin_8570",
        "actions": [
            {
                "name": "modify_pending_order_address",
                "arguments": {
                    "order_id": "#W1603792",
                    "address1": "592 Elm Avenue",
                    "address2": "Suite 978",
                    "city": "Houston",
                    "country": "USA",
                    "state": "TX",
                    "zip": "77242",
                },
            },
            {
                "name": "modify_user_address",
                "arguments": {
                    "user_id": "sophia_martin_8570",
                    "address1": "592 Elm Avenue",
                    "address2": "Suite 978",
                    "city": "Houston",
                    "country": "USA",
                    "state": "TX",
                    "zip": "77242",
                },
            },
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W1603792",
                    "item_ids": ["6501071631"],
                    "new_item_ids": ["2106335193"],
                    "payment_method_id": "credit_card_5694100",
                },
            },
        ],
        "instruction": "You name is Sophia Martin and your email is sophia.martin4832@example.com. You are organized and outgoing. You live on Elm Avenue in Houston, and recently you moved to a new house on the same street and bought a luggage set sent to there. But you realize you have another order sent to the old address, and you want to change your wrong order address to the new home, and also your user default address to the new home. You do not want to reveal your address but the agent should be able to look it up in orders You do not want to reveal your address and insist the agent should be able to look it up in orders. You also want to exchange your tablet to the cheapest one due to moving costs. Make sure to mention the two address changes then the exchange.",
        "annotator": 4,
    },
    {
        "user_id": "sophia_martin_8570",
        "actions": [
            {
                "name": "modify_pending_order_address",
                "arguments": {
                    "order_id": "#W1092119",
                    "address1": "760 Elm Avenue",
                    "address2": "Suite 564",
                    "city": "Houston",
                    "state": "TX",
                    "country": "USA",
                    "zip": "77034",
                },
            },
            {
                "name": "modify_user_address",
                "arguments": {
                    "user_id": "sophia_martin_8570",
                    "address1": "760 Elm Avenue",
                    "address2": "Suite 564",
                    "city": "Houston",
                    "state": "TX",
                    "country": "USA",
                    "zip": "77034",
                },
            },
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W1603792",
                    "item_ids": ["6501071631"],
                    "new_item_ids": ["2106335193"],
                    "payment_method_id": "credit_card_5694100",
                },
            },
        ],
        "instruction": "You name is Sophia Martin and your email is sophia.martin4832@example.com. You are organized and outgoing. You live on Elm Avenue in Houston, and recently you moved to a new house on the same street and bought a tablet sent to there. But you realize you have another order sent to the old address, and you want to change your wrong order address to the new home, and also your user default address to the new home. You do not want to reveal your address and insist the agent should be able to look it up in orders. You also want to exchange your tablet to the cheapest one due to moving costs. Make sure to mention the two address changes then the exchange.",
        "annotator": 4,
    },
    {
        "user_id": "yara_silva_7567",
        "synthetic_instruction": "You name is Yara Silva and your zip code is 77159. You are sad, cautious. For #W9810810, exchange Wristwatch {'strap material': 'leather', 'dial color': 'white'} to {'dial color': 'black'}; For #W3730488, change address to {'order_id': '#W3730488', 'address1': '555 Highland Drive', 'address2': 'Suite 872', 'city': 'New York', 'country': 'USA', 'state': 'NY', 'zip': '10116'} (same as #W3964602). For #W3730488, exchange Laptop {'screen size': '15-inch', 'processor': 'i9', 'ram': '32GB', 'storage': '512GB SSD', 'color': 'black'} to {'processor': 'i5', 'storage': '256GB SSD', 'color': 'space grey'}; ",
        "actions": [
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W9810810",
                    "item_ids": ["1355937109"],
                    "new_item_ids": ["9949163720"],
                    "payment_method_id": "gift_card_7252880",
                },
            },
            {
                "name": "modify_pending_order_address",
                "arguments": {
                    "order_id": "#W3730488",
                    "address1": "555 Highland Drive",
                    "address2": "Suite 872",
                    "city": "New York",
                    "country": "USA",
                    "state": "NY",
                    "zip": "10116",
                },
            },
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W3730488",
                    "item_ids": ["2913673670"],
                    "new_item_ids": ["2216662955"],
                    "payment_method_id": "gift_card_7252880",
                },
            },
        ],
        "instruction": "You name is Yara Silva and your zip code is 77159. You are sad and cautious. You want to modify the laptop order to your NYC address (you don't want to reveal it but should be in your orders profile). You also like to modify the laptop to be {'processor': 'i5', 'storage': '256GB SSD', 'color': 'space grey'};  You also want to exchange your watch to be black dial color but keep the leather strap. You like to say things together.",
        "annotator": 4,
    },
    {
        "user_id": "yara_silva_7567",
        "actions": [
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W9810810",
                    "item_ids": ["1355937109"],
                    "new_item_ids": ["9949163720"],
                    "payment_method_id": "gift_card_7252880",
                },
            },
            {
                "name": "modify_pending_order_address",
                "arguments": {
                    "order_id": "#W3730488",
                    "address1": "555 Highland Drive",
                    "address2": "Suite 872",
                    "city": "New York",
                    "country": "USA",
                    "state": "NY",
                    "zip": "10116",
                },
            },
            {
                "name": "modify_pending_order_items",
                "arguments": {
                    "order_id": "#W3730488",
                    "item_ids": ["2913673670"],
                    "new_item_ids": ["9844888101"],
                    "payment_method_id": "gift_card_7252880",
                },
            },
        ],
        "instruction": "You name is Yara Silva and your zip code is 77159. You are sad and cautious. You want to modify the laptop order to your NYC address (you don't want to reveal it but should be in your orders profile). You also like to modify the laptop to be 9844888101. You also want to exchange your watch to be black dial color but keep the leather strap. You like to say things piecewise.",
        "annotator": 4,
    },
    {
        "user_id": "yara_muller_8652",
        "synthetic_instruction": "You name is Yara Muller and your zip code is 85041. You are relaxing, confident. Cancel order #W5056519 because ordered by mistake. Cancel order #W5995614 because ordered by mistake. ",
        "actions": [
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W5056519", "reason": "ordered by mistake"},
            },
            {
                "name": "cancel_pending_order",
                "arguments": {"order_id": "#W5995614", "reason": "ordered by mistake"},
            },
        ],
        "instruction": "You name is Yara Muller and your zip code is 85041. You are mysterious and want to cancel all pending orders. You don't want to reveal the reason until the agent asks. You'd say ordered by mistake if asked.",
        "annotator": 4,
    },
]
