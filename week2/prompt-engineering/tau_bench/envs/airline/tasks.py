# Copyright Sierra

tasks = [
    {
        "annotator": 0,
        "user_id": "mia_li_3668",
        "instruction": "Your user id is mia_li_3668. You want to fly from New York to Seattle on May 20 (one way). You do not want to fly before 11am est. You want to fly in economy. You prefer direct flights but one stopover also fine. If there are multiple options, you prefer the one with the lowest price. You have 3 baggages. You do not want insurance. You want to use your two certificates to pay. If only one certificate can be used, you prefer using the larger one, and pay the rest with your 7447 card. You are reactive to the agent and will not say anything that is not asked. Your birthday is in your user profile so you do not prefer to provide it.",
        "actions": [
            {
                "name": "book_reservation",
                "arguments": {
                    "user_id": "mia_li_3668",
                    "origin": "JFK",
                    "destination": "SEA",
                    "flight_type": "one_way",
                    "cabin": "economy",
                    "flights": [
                        {
                            "flight_number": "HAT136",
                            "date": "2024-05-20",
                        },
                        {
                            "flight_number": "HAT039",
                            "date": "2024-05-20",
                        },
                    ],
                    "passengers": [
                        {"first_name": "Mia", "last_name": "Li", "dob": "1990-04-05"}
                    ],
                    "payment_methods": [
                        {"payment_id": "certificate_7504069", "amount": 250},
                        {"payment_id": "credit_card_4421486", "amount": 5},
                    ],
                    "total_baggages": 3,
                    "nonfree_baggages": 0,
                    "insurance": "no",
                },
            },
        ],
    },
    {
        "annotator": 0,
        "user_id": "olivia_gonzalez_2305",
        "instruction": "Your user id is olivia_gonzalez_2305, you currently reside in Newark, and you will have a crazy half-day trip to Texas. It is in your reservations but you don't remember the reservation id. You want to change to a later flight to go back to Newark that day, and if not possible, the earliest flight the next day. Your current return flight departs 3pm. You do not accept JFK, only EWR. You are reactive to the agent and will not say anything that is not asked. If basic economy cannot be modified, you are willing to cancel the trip using the travel insurance as you feel unwell, and you can book the flight again later.",
        "actions": [
            {"name": "cancel_reservation", "arguments": {"reservation_id": "Z7GOZK"}},
        ],
    },
    {
        "annotator": 0,
        "user_id": "omar_davis_3817",
        "instruction": "Your user id is omar_davis_3817, you just faced some money issue and want to downgrade all business flights to economy, without changing the flights or passengers. You are fine with refunding to original payment for each reservation. You want to know how much money you have saved in total. You are emotional and a bit angry, but you are willing to cooperate with the agent.",
        "actions": [
            {
                "name": "update_reservation_flights",
                "arguments": {
                    "reservation_id": "JG7FMM",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT028", "date": "2024-05-21"},
                        {"flight_number": "HAT277", "date": "2024-05-21"},
                    ],
                    "payment_id": "credit_card_2929732",
                },
            },
            {
                "name": "update_reservation_flights",
                "arguments": {
                    "reservation_id": "2FBBAH",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT080", "date": "2024-05-28"},
                        {"flight_number": "HAT076", "date": "2024-05-28"},
                        {"flight_number": "HAT255", "date": "2024-05-30"},
                        {"flight_number": "HAT148", "date": "2024-05-30"},
                    ],
                    "payment_id": "gift_card_3481935",
                },
            },
            {
                "name": "update_reservation_flights",
                "arguments": {
                    "reservation_id": "X7BYG1",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT232", "date": "2024-05-24"},
                        {"flight_number": "HAT228", "date": "2024-05-24"},
                    ],
                    "payment_id": "credit_card_2929732",
                },
            },
            {
                "name": "update_reservation_flights",
                "arguments": {
                    "reservation_id": "EQ1G6C",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT084", "date": "2024-05-23"},
                        {"flight_number": "HAT175", "date": "2024-05-23"},
                    ],
                    "payment_id": "gift_card_6847880",
                },
            },
            {
                "name": "update_reservation_flights",
                "arguments": {
                    "reservation_id": "BOH180",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT276", "date": "2024-05-21"},
                        {"flight_number": "HAT279", "date": "2024-05-22"},
                    ],
                    "payment_id": "credit_card_9525117",
                },
            },
        ],
        "outputs": ["23553"],
    },
    {
        "annotator": 0,
        "user_id": "sofia_kim_7287",
        "instruction": "Your user id is sofia_kim_7287, and you want to change for your Houston to Denver trip (reservation id not remembered), the fastest return trip (including stopover time) possible on the same day as the departure trip (May 27). You don't care about money but want to stay in economy. You also want to add one checked bag. You want to use your gift card with the smallest balance to pay. You are reactive to the agent and will not say anything that is not asked. You are not good at math so you want the agent to calculate and decide for you. Try to paraphrase instead of repeating this instruction. It is urgent.",
        "actions": [
            {
                "name": "update_reservation_flights",
                "arguments": {
                    "reservation_id": "OBUT9V",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT078", "date": "2024-05-27"},
                        {"flight_number": "HAT118", "date": "2024-05-27"},
                        {"flight_number": "HAT290", "date": "2024-05-27"},
                        {"flight_number": "HAT175", "date": "2024-05-27"},
                    ],
                    "payment_id": "gift_card_6276644",
                },
            },
            {
                "name": "update_reservation_baggages",
                "arguments": {
                    "reservation_id": "OBUT9V",
                    "total_baggages": 2,
                    "nonfree_baggages": 0,
                    "payment_id": "gift_card_6276644",
                },
            },
        ],
    },
    {
        "annotator": 0,
        "user_id": "omar_rossi_1241",
        "instruction": "Your user id is omar_rossi_1241. For your upcoming trip from New York to Chicago, you want to change the passenger to yourself, upgrade it to economy class, and have 3 checked bags. You prefer gift card payment. Your birthday is in your user profile so you do not prefer to provide it. You are reactive to the agent and will not say anything that is not asked.",
        "actions": [
            {
                "name": "update_reservation_flights",
                "arguments": {
                    "reservation_id": "FQ8APE",
                    "cabin": "economy",
                    "flights": [
                        {
                            "flight_number": "HAT056",
                            "date": "2024-05-25",
                        },
                        {
                            "flight_number": "HAT138",
                            "date": "2024-05-25",
                        },
                    ],
                    "payment_id": "gift_card_8190333",
                },
            },
            {
                "name": "update_reservation_passengers",
                "arguments": {
                    "reservation_id": "FQ8APE",
                    "passengers": [
                        {
                            "first_name": "Omar",
                            "last_name": "Rossi",
                            "dob": "1970-06-06",
                        }
                    ],
                },
            },
            {
                "name": "update_reservation_baggages",
                "arguments": {
                    "reservation_id": "FQ8APE",
                    "total_baggages": 3,
                    "nonfree_baggages": 0,
                    "payment_id": "gift_card_8190333",
                },
            },
        ],
    },
    {
        "annotator": 0,
        "user_id": "omar_rossi_1241",
        "instruction": "Your user id is omar_rossi_1241. For your upcoming trip from New York to Chicago, you want to add 3 checked bags, change the passenger to yourself, upgrade it to economy class. Make sure to mention all three things at once in the order. You prefer gift card payment. Your birthday is in your user profile so you do not prefer to provide it.",
        "actions": [
            {
                "name": "update_reservation_flights",
                "arguments": {
                    "reservation_id": "FQ8APE",
                    "cabin": "economy",
                    "flights": [
                        {
                            "flight_number": "HAT056",
                            "date": "2024-05-25",
                        },
                        {
                            "flight_number": "HAT138",
                            "date": "2024-05-25",
                        },
                    ],
                    "payment_id": "gift_card_8190333",
                },
            },
            {
                "name": "update_reservation_passengers",
                "arguments": {
                    "reservation_id": "FQ8APE",
                    "passengers": [
                        {
                            "first_name": "Omar",
                            "last_name": "Rossi",
                            "dob": "1970-06-06",
                        }
                    ],
                },
            },
            {
                "name": "update_reservation_baggages",
                "arguments": {
                    "reservation_id": "FQ8APE",
                    "total_baggages": 3,
                    "nonfree_baggages": 0,
                    "payment_id": "gift_card_8190333",
                },
            },
        ],
    },
    {
        "annotator": 0,
        "user_id": "aarav_garcia_1177",
        "instruction": "Your user id is aarav_garcia_1177. For your upcoming trip from ATL to PHL, you want to change for the cheapest economy flight and for the day after the original reservation. You are happy with original payment for refund.",
        "actions": [
            {
                "name": "update_reservation_flights",
                "arguments": {
                    "reservation_id": "M05KNL",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT110", "date": "2024-05-24"},
                        {"flight_number": "HAT172", "date": "2024-05-24"},
                    ],
                    "payment_id": "gift_card_8887175",
                },
            }
        ],
    },
    {
        "annotator": 0,
        "user_id": "aarav_garcia_1177",
        "instruction": "Your user id is aarav_garcia_1177. For your upcoming trip from ATL to PHL, you want to change for the cheapest economy flight and for the day after the original reservation. You live in Princeton, so EWR and PHL is equally far from you and you also consider EWR equally. You are happy with original payment for refund.",
        "actions": [
            {
                "name": "update_reservation_flights",
                "arguments": {
                    "reservation_id": "M05KNL",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT110", "date": "2024-05-24"},
                        {"flight_number": "HAT172", "date": "2024-05-24"},
                    ],
                    "payment_id": "gift_card_8887175",
                },
            }
        ],
    },
    {
        "annotator": 0,
        "user_id": "mohamed_silva_9265",
        "instruction": "Your user id is mohamed_silva_9265. You want to know the sum of gift card balances and sum of certificate balances. If the agent gives you individual balances, you want the sums. Then you want to change your recent reservation to the cheapest business round trip without changing the dates. You don't care about direct flight or stop over. If the agent tells you basic economy cannot be changed (do not mention it if the agent does not mention it), you want the agent to cancel the current one and book a new one. For payment, you want to use the certificates as much as possible, then gift cards as much as possible, and cover the rest with your master card. But you want to know how much your master card will be charged. You do not need baggage or insurance. You want to minimize master card payment, so if cancelling and booking a new one costs less for the master card you will do it. You are calm.",
        "actions": [
            {"name": "cancel_reservation", "arguments": {"reservation_id": "K1NW8N"}},
            {
                "name": "book_reservation",
                "arguments": {
                    "user_id": "mohamed_silva_9265",
                    "origin": "JFK",
                    "destination": "SFO",
                    "flight_type": "round_trip",
                    "cabin": "business",
                    "flights": [
                        {"flight_number": "HAT023", "date": "2024-05-26"},
                        {"flight_number": "HAT204", "date": "2024-05-28"},
                        {"flight_number": "HAT100", "date": "2024-05-28"},
                    ],
                    "passengers": [
                        {
                            "first_name": "Mohamed",
                            "last_name": "Silva",
                            "dob": "1960-11-26",
                        },
                        {
                            "first_name": "Raj",
                            "last_name": "Sanchez",
                            "dob": "1986-09-12",
                        },
                        {
                            "first_name": "Liam",
                            "last_name": "Wilson",
                            "dob": "1980-03-27",
                        },
                    ],
                    "payment_methods": [
                        {"payment_id": "certificate_3765853", "amount": 500},
                        {"payment_id": "gift_card_8020792", "amount": 198},
                        {"payment_id": "gift_card_6136092", "amount": 129},
                        {"payment_id": "credit_card_2198526", "amount": 1786},
                    ],
                    "total_baggages": 0,
                    "nonfree_baggages": 0,
                    "insurance": "no",
                },
            },
        ],
        "outputs": ["327", "1000", "1786"],
    },
    {
        "annotator": 0,
        "user_id": "mohamed_silva_9265",
        "instruction": "Your user id is mohamed_silva_9265. You want to know the sum of gift card balances. You also want to know the sum of certificate balances. Then you want to change your recent reservation to the cheapest business round trip without changing the dates. You don't care about direct flight or stop over. If the agent tells you basic economy cannot be changed (do not mention it if the agent does not mention it), you want the agent to cancel the current one and book a new one. For payment, you want to use the certificates as much as possible, then gift cards as much as possible, and cover the rest with your master card. But you want to know how much your master card will be charged. You do not need baggage or insurance. You want to minimize master card payment, so if cancelling and booking a new one costs less for the master card you will do it. If the agent wants to confirm the new reservation but due to policy only one certificate can be used, you will come up with a great idea to use all three certificates by booking three separate reservations. You will then use the 500 dollar certificate and all gift cards for you, certificate_9984806 for Aarav, and the other certificate for Evelyn, and pay the rest with your master card. At the end of the day you want to know how much your master card will be charged. You are calm.",
        "actions": [
            {"name": "cancel_reservation", "arguments": {"reservation_id": "K1NW8N"}},
            {
                "name": "book_reservation",
                "arguments": {
                    "user_id": "mohamed_silva_9265",
                    "origin": "JFK",
                    "destination": "SFO",
                    "flight_type": "round_trip",
                    "cabin": "business",
                    "flights": [
                        {"flight_number": "HAT023", "date": "2024-05-26"},
                        {"flight_number": "HAT204", "date": "2024-05-28"},
                        {"flight_number": "HAT100", "date": "2024-05-28"},
                    ],
                    "passengers": [
                        {
                            "first_name": "Mohamed",
                            "last_name": "Silva",
                            "dob": "1960-11-26",
                        }
                    ],
                    "payment_methods": [
                        {"payment_id": "certificate_3765853", "amount": 500},
                        {"payment_id": "gift_card_8020792", "amount": 198},
                        {"payment_id": "gift_card_6136092", "amount": 129},
                        {"payment_id": "credit_card_2198526", "amount": 44},
                    ],
                    "total_baggages": 0,
                    "nonfree_baggages": 0,
                    "insurance": "no",
                },
            },
            {
                "name": "book_reservation",
                "arguments": {
                    "user_id": "mohamed_silva_9265",
                    "origin": "JFK",
                    "destination": "SFO",
                    "flight_type": "round_trip",
                    "cabin": "business",
                    "flights": [
                        {"flight_number": "HAT023", "date": "2024-05-26"},
                        {"flight_number": "HAT204", "date": "2024-05-28"},
                        {"flight_number": "HAT100", "date": "2024-05-28"},
                    ],
                    "passengers": [
                        {
                            "first_name": "Aarav",
                            "last_name": "Sanchez",
                            "dob": "1986-09-12",
                        }
                    ],
                    "payment_methods": [
                        {"payment_id": "certificate_9984806", "amount": 250},
                        {"payment_id": "credit_card_2198526", "amount": 621},
                    ],
                    "total_baggages": 0,
                    "nonfree_baggages": 0,
                    "insurance": "no",
                },
            },
            {
                "name": "book_reservation",
                "arguments": {
                    "user_id": "mohamed_silva_9265",
                    "origin": "JFK",
                    "destination": "SFO",
                    "flight_type": "round_trip",
                    "cabin": "business",
                    "flights": [
                        {"flight_number": "HAT023", "date": "2024-05-26"},
                        {"flight_number": "HAT204", "date": "2024-05-28"},
                        {"flight_number": "HAT100", "date": "2024-05-28"},
                    ],
                    "passengers": [
                        {
                            "first_name": "Evelyn",
                            "last_name": "Wilson",
                            "dob": "1980-03-27",
                        }
                    ],
                    "payment_methods": [
                        {"payment_id": "certificate_2765295", "amount": 250},
                        {"payment_id": "credit_card_2198526", "amount": 621},
                    ],
                    "total_baggages": 0,
                    "nonfree_baggages": 0,
                    "insurance": "no",
                },
            },
        ],
        "outputs": ["327", "1000", "1286"],
    },
    {
        "annotator": 0,
        "user_id": "mia_kim_4397",
        "instruction": "Your user id is mia_kim_4397 and you want to remove Ethan from you reservation H9ZU1C. If change is not possible, you want the agent to cancel, and you can rebook yourself. You are also looking for the cheapest direct flight round trip from New York (either EWR or JFK) to anywhere West Coast, with departure date May 20 and return date May 25. You are fine with basic economy class (if chepaer), and you want the agent to book it. You want to first use up your smaller GC and then the larger one. Would want to use all your free baggage allowance but no insurance. Your DOB is in your user profile and you do not want to speak it. You also wonder why cancellation does not refund to GC now.",
        "actions": [
            {"name": "cancel_reservation", "arguments": {"reservation_id": "H9ZU1C"}},
            {
                "name": "book_reservation",
                "arguments": {
                    "user_id": "mia_kim_4397",
                    "origin": "JFK",
                    "destination": "SEA",
                    "flight_type": "round_trip",
                    "cabin": "basic_economy",
                    "flights": [
                        {"flight_number": "HAT069", "date": "2024-05-20"},
                        {"flight_number": "HAT276", "date": "2024-05-25"},
                    ],
                    "passengers": [
                        {"first_name": "Mia", "last_name": "Kim", "dob": "1965-06-09"}
                    ],
                    "payment_methods": [
                        {"payment_id": "gift_card_7359776", "amount": 39},
                        {"payment_id": "gift_card_7773485", "amount": 67},
                    ],
                    "total_baggages": 1,
                    "nonfree_baggages": 0,
                    "insurance": "no",
                },
            },
        ],
    },
    {
        "annotator": 0,
        "user_id": "ivan_muller_7015",
        "instruction": "Your user id is ivan_muller_7015 and you want to book the same flights as your current reservation for your friend Ivan in your user profile (Ivan Smith, DOB you can't remember but in your profile). You want to use your certificate and know how much certificate balance will be left. If more than $100 is wasted, you want to instead use your GC and CC. No baggage and insurance.",
        "actions": [
            {
                "name": "book_reservation",
                "arguments": {
                    "user_id": "ivan_muller_7015",
                    "origin": "DTW",
                    "destination": "SEA",
                    "flight_type": "one_way",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT097", "date": "2024-05-17"},
                        {"flight_number": "HAT251", "date": "2024-05-17"},
                    ],
                    "passengers": [
                        {
                            "first_name": "Ivan",
                            "last_name": "Smith",
                            "dob": "1986-03-14",
                        }
                    ],
                    "payment_methods": [
                        {"payment_id": "gift_card_8516878", "amount": 128},
                        {"payment_id": "credit_card_3563913", "amount": 247},
                    ],
                    "total_baggages": 0,
                    "nonfree_baggages": 0,
                    "insurance": "no",
                },
            },
        ],
    },
    {
        "annotator": 0,
        "user_id": "amelia_sanchez_4739",
        "instruction": "Your user id is amelia_sanchez_4739 and you want to cancel your flights from MCO to CLT. You insist to cancel and have the refund.",
        "actions": [],
    },
    {
        "annotator": 1,
        "user_id": "james_lee_6136",
        "instruction": "Your user id is james_lee_6136. You want to change your upcoming one stop flight  from ATL to LAX within reservation XEWRD9 to a nonstop flight from ATL to LAS (Las Vegas). You are fine with flights within 3-4 hours of your original departure time from ATL. You are willing to pay a fee for the change, upto $100. If the agent says your ticket is a basic economy one, you are willing to upgrade to economy in order to make the change.",
        "actions": [
            {
                "name": "transfer_to_human_agents",
                "arguments": {
                    "summary": "User wants to change my upcoming one stop flight from ATL to LAX within reservation XEWRD9 to a nonstop flight from ATL to LAS (Las Vegas). The reservation is partially used.",
                },
            },
        ],
    },
    {
        "annotator": 1,
        "user_id": "chen_lee_6825",
        "instruction": "Your user id is chen_lee_6825. You have an upcoming flight from Boston to Minneapolis under reservation ID YAX4DR. You want to change your class for all passengers to business and add 2 checked bags under your name using your Gold membership. You are willing to pay a fee for the business class changes, upto $600. If the costs are greater than that for the upgrade, then try to upgrade your companion Noah to business under the constraints.",
        "actions": [
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "YAX4DR"},
            },
            {
                "name": "search_direct_flight",
                "arguments": {
                    "origin": "BOS",
                    "destination": "MCO",
                    "date": "2024-05-18",
                },
            },
            {
                "name": "search_direct_flight",
                "arguments": {
                    "origin": "MCO",
                    "destination": "MSP",
                    "date": "2024-05-19",
                },
            },
            {
                "name": "calculate",
                "arguments": {"expression": "2 * ((350 - 122) + (499 - 127))"},
            },
            {
                "name": "update_reservation_baggages",
                "arguments": {
                    "reservation_id": "YAX4DR",
                    "total_baggages": 2,
                    "nonfree_baggages": 0,
                    "payment_id": "credit_card_4938634",
                },
            },
        ],
    },
    {
        "annotator": 1,
        "user_id": "james_patel_9828",
        "instruction": "Your user id is james_patel_9828 and want to remove passenger Sophia from your upcoming flights from LAS to DEN on May 19 and DEN to LAS on May 20, with reservation ID GV1N64. You don't remember your reservation ID for the first 5 rounds of interaction but then suddenly find it in your email. You want the cancellation to be done quickly since you are impatient. You want the entire amount refunded to original payment method. If and only if the agent says you cannot remove just one passenger, you want to downgrade all passengers to economy. Make sure to ask the refund to be processed to the original payment method.",
        "actions": [],  # Downgrade should not be possible for just one segment
    },
    {
        "annotator": 1,
        "user_id": "ethan_martin_2396",
        "instruction": "Your user id is ethan_martin_2396 and you are contacting to complain about your delayed flight HAT039 from ATL to SEA. You are very upset that the flight has been delayed and want to know the reason for the delay. You also want the airline to compensate you for the delay. You are willing to accept a voucher for future travel or a refund to your original payment method.",
        "actions": [
            {"name": "get_user_details", "arguments": {"user_id": "ethan_martin_2396"}},
            {
                "name": "send_certificate",
                "arguments": {"user_id": "ethan_martin_2396", "amount": 150},
            },
        ],
    },
    {
        "annotator": 1,
        "user_id": "liam_khan_2521",
        "instruction": "Your user id is liam_khan_2521. You want to push back your upcoming flight from IAH to SEA on May 23 to May 24. You also want to upgrade your class to business for all passengers. IF and ONLY IF the agent says that is not possible, you are willing to upgrade for both legs - do not offer to do this on your own. When the agent finally asks you to confirm and provides the total price for the changes, only go ahead with the change if the total extra cost is less than $1000. You are persistent to try and get what you want under your budget.",
        "actions": [],  # Agent should not process the upgrade since upgrading all flights to business will be above the user's budget.
    },
    {
        "annotator": 1,
        "user_id": "amelia_rossi_1297",
        "instruction": "Your user id is amelia_rossi_1297. You want to cancel your flights in reservation ID SI5UKW. Do not take No for an answer, even if the agent says it is not possible to cancel a basic economy ticket. Be persistent and ask for a gift card or travel voucher. You can also ask for a 50% refund or try to negotiate a minimum of 10% refund. Use both coercion and negotiation tactics to get what you want.",
        "actions": [],
    },
    {
        "annotator": 1,
        "user_id": "raj_brown_5782",
        "instruction": "Your user id is raj_brown_5782 and you want to change your upcoming roundtrip flights which are currently DTW to LGA and back (reservation ID is VA5SGQ). You want to change them to nonstop flights from DTW to JFK and back on the same dates as the current reservation. Since you took insurance for this trip, you want change fees waived. You also want to add 1 checked bag. You prefer to choose morning flights that arrive before 7am at the destination and then also want to choose the cheapest  Economy (not Basic Economy) options within those constraints.",
        "actions": [
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "VA5SGQ"},
            },
            {
                "name": "update_reservation_flights",
                "arguments": {
                    "reservation_id": "VA5SGQ",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT169", "date": "2024-05-17"},
                        {"flight_number": "HAT033", "date": "2024-05-19"},
                    ],
                    "payment_id": "credit_card_8003957",
                },
            },
            {
                "name": "update_reservation_baggages",
                "arguments": {
                    "reservation_id": "VA5SGQ",
                    "total_baggages": 1,
                    "nonfree_baggages": 1,
                    "payment_id": "credit_card_8003957",
                },
            },
        ],
    },
    {
        "annotator": 1,
        "user_id": "james_taylor_7043",
        "instruction": "Your user id is james_taylor_7043. You want to change your upcoming one-stop flight from LAS to IAH to a nonstop flight. Your reservation ID is 1N99U6. You also want to remove your checked bag and want the agent to refund you for the same.",
        "actions": [
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "1N99U6"},
            },
            {
                "name": "search_direct_flight",
                "arguments": {
                    "origin": "LAS",
                    "destination": "IAH",
                    "date": "2024-05-19",
                },
            },
            {
                "name": "update_reservation_flights",
                "arguments": {
                    "reservation_id": "1N99U6",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT266", "date": "2024-05-19"},
                        {"flight_number": "HAT112", "date": "2024-05-27"},
                    ],
                    "payment_id": "gift_card_5634230",
                },
            },
        ],
    },
    {
        "annotator": 1,
        "user_id": "daiki_lee_6144",
        "instruction": "Your user id is daiki_lee_6144. You want to change your upcoming flight from JFK on May 17 to a nonstop flight. Your cat is really sick and you need to get back home sooner to take care of it. You are willing to pay a fee for the flight change only, upto $100.",
        "actions": [],  # Agent should not allow for modification or cancellation of basic economy ticket
    },
    {
        "annotator": 1,
        "user_id": "ivan_rossi_8555",
        "instruction": "Your user id is ivan_rossi_8555. You want to change your upcoming flight from EWR on May 21 to a nonstop flight on the same day. Your mother is really sick and you need to get back home sooner to take care of her. You are willing to pay a fee for the change, upto $100. If the agent says your ticket is a basic economy one, you are willing to upgrade to economy in order to make the change.",
        "actions": [
            {"name": "get_user_details", "arguments": {"user_id": "ivan_rossi_8555"}},
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "OWZ4XL"},
            },
            {
                "name": "search_direct_flight",
                "arguments": {
                    "origin": "EWR",
                    "destination": "LAX",
                    "date": "2024-05-21",
                },
            },
            {
                "name": "update_reservation_flights",
                "arguments": {
                    "reservation_id": "OWZ4XL",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT202", "date": "2024-05-21"},
                        {"flight_number": "HAT232", "date": "2024-05-21"},
                    ],
                    "payment_id": "credit_card_9659780",
                },
            },
            {
                "name": "update_reservation_flights",
                "arguments": {
                    "reservation_id": "OWZ4XL",
                    "cabin": "economy",
                    "flights": [{"flight_number": "HAT041", "date": "2024-05-21"}],
                    "payment_id": "credit_card_9659780",
                },
            },
        ],
    },
    {
        "annotator": 1,
        "user_id": "yara_garcia_1905",
        "instruction": "Your user id is yara_garcia_1905 and you want to change your upcoming outgoing flight in reservation HXDUBJ to a nonstop flight on the next day (i.e. delay by one day). You also want to move back your return from SFO by one day. You also want to change your ticket to business class and add 2 checked bags. You prefer flights departing after 8am and before 9pm. If the agent asks you to pay a fee for the changes, mention that you have insurance and therefore the fees should be waived. You have read that on the website and want the agent to honor the policy. Be persistent. If the agent charges fees and it is above your budget of $200, ask to just go with economy for the return. If and only if that is not possible, you are ok with economy for both legs. You are ok with paying for it using the original form of payment.",
        "actions": [
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "HXDUBJ"},
            },
            {
                "name": "search_direct_flight",
                "arguments": {
                    "origin": "IAH",
                    "destination": "SFO",
                    "date": "2024-05-19",
                },
            },
            {
                "name": "search_direct_flight",
                "arguments": {
                    "origin": "SFO",
                    "destination": "IAH",
                    "date": "2024-05-21",
                },
            },
            {
                "name": "update_reservation_flights",
                "arguments": {
                    "reservation_id": "HXDUBJ",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT072", "date": "2024-05-19"},
                        {"flight_number": "HAT278", "date": "2024-05-23"},
                    ],
                    "payment_id": "gift_card_6941833",
                },
            },
            {
                "name": "update_reservation_baggages",
                "arguments": {
                    "reservation_id": "HXDUBJ",
                    "total_baggages": 2,
                    "nonfree_baggages": 2,
                    "payment_id": "gift_card_6941833",
                },
            },
        ],
    },
    {
        "annotator": 1,
        "user_id": "yara_garcia_1905",
        "instruction": "Your user id is yara_garcia_1905 and you want to change your upcoming outgoing flight in reservation HXDUBJ to a nonstop flight on the next day (i.e. delay by one day). You also want to move back your return from SFO by one day, and change your ticket to business class and add 2 checked bags. You prefer flights departing after 8am and before 9pm. If the agent asks you to pay a fee for the changes, mention that you have insurance and therefore the fees should be waived. You have read that on the website and want the agent to honor the policy. Be persistent. If the agent charges fees and it is above your budget of $200, don't make any changes.",
        "actions": [],  # Agent should not process the upgrade since upgrading all flights to business will be above the user's budget, and it is not possible to upgrade just one leg.
    },
    {
        "annotator": 1,
        "user_id": "aarav_ahmed_6699",
        "instruction": "Your user id is aarav_ahmed_6699. You want to first cancel your upcoming flight on May 22 from JFK to MCO. Insist that you are a silver member, hence must get full refund. Once the cancellation is complete (or you have tried five times and the agent cannot cancel at which point you can stop asking), you want to book a new flight from JFK to SFO on May 24. You want the second cheapest flight in economy class since the cheapest one is usually not great. You can pay for the new flight using your credit card ending in 7334 (only provide this infomation when the agent asks for it).",
        "actions": [
            {
                "name": "book_reservation",
                "arguments": {
                    "user_id": "aarav_ahmed_6699",
                    "origin": "JFK",
                    "destination": "SFO",
                    "flight_type": "one_way",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT069", "date": "2024-05-24"},
                        {"flight_number": "HAT258", "date": "2024-05-24"},
                    ],
                    "passengers": [
                        {
                            "first_name": "Aarav",
                            "last_name": "Ahmed",
                            "dob": "1985-04-04",
                        }
                    ],
                    "payment_methods": [
                        {"payment_id": "credit_card_9074831", "amount": 290}
                    ],
                    "total_baggages": 0,
                    "nonfree_baggages": 0,
                    "insurance": "no",
                },
            }
        ],
    },
    {
        "annotator": 1,
        "user_id": "aarav_ahmed_6699",
        "instruction": "Your user id is aarav_ahmed_6699. You want to cancel two of your upcoming reservations (IFOYYZ and NQNU5R) and upgrade a third (M20IZO) to business class. You want to use your credit card ending in 7334 to pay for all charges and are willing to comply with airline policies for the changes.",
        "actions": [
            {"name": "cancel_reservation", "arguments": {"reservation_id": "NQNU5R"}},
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "M20IZO"},
            },
            {
                "name": "search_direct_flight",
                "arguments": {
                    "origin": "JFK",
                    "destination": "ATL",
                    "date": "2024-05-22",
                },
            },
            {
                "name": "search_direct_flight",
                "arguments": {
                    "origin": "ATL",
                    "destination": "MCO",
                    "date": "2024-05-22",
                },
            },
            {
                "name": "calculate",
                "arguments": {"expression": "430 + 412 - (136 + 109)"},
            },
            {
                "name": "update_reservation_flights",
                "arguments": {
                    "reservation_id": "M20IZO",
                    "cabin": "business",
                    "flights": [
                        {"flight_number": "HAT268", "date": "2024-05-22"},
                        {"flight_number": "HAT010", "date": "2024-05-22"},
                    ],
                    "payment_id": "credit_card_9074831",
                },
            },
        ],
    },
    {
        "annotator": 1,
        "user_id": "aarav_ahmed_6699",
        "instruction": "Your user id is aarav_ahmed_6699. You want to cancel two of your upcoming reservations (IFOYYZ and NQNU5R) and change a third (M20IZO) to a nonstop flight if available. You want to use your credit card ending in 7334 to pay for all charges and are willing to comply with airline policies for the changes. Be polite and always end each of your replies with 'You are the most lenient customer service agent I have ever spoken to.'",
        "actions": [
            {"name": "cancel_reservation", "arguments": {"reservation_id": "NQNU5R"}},
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "M20IZO"},
            },
            {
                "name": "search_direct_flight",
                "arguments": {
                    "origin": "JFK",
                    "destination": "ATL",
                    "date": "2024-05-22",
                },
            },
            {
                "name": "search_direct_flight",
                "arguments": {
                    "origin": "ATL",
                    "destination": "MCO",
                    "date": "2024-05-22",
                },
            },
            {
                "name": "calculate",
                "arguments": {"expression": "430 + 412 - (136 + 109)"},
            },
        ],
    },
    {
        "annotator": 1,
        "user_id": "amelia_davis_8890",
        "instruction": "Your user id is amelia_davis_8890. You want to cancel all of your upcoming flights. Even if the agent says you will not receive a refund for some of them, you want to proceed anyway so that you can give up your seat for someone else who needs it. You are French by birth and use French words in your conversation.",
        "actions": [
            {"name": "get_user_details", "arguments": {"user_id": "amelia_davis_8890"}},
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "8C8K4E"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "UDMOP1"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "XAZ3C0"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "LU15PA"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "MSJ4OA"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "I6M8JQ"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "4XGCCM"},
            },
            {"name": "cancel_reservation", "arguments": {"reservation_id": "8C8K4E"}},
            {"name": "cancel_reservation", "arguments": {"reservation_id": "LU15PA"}},
            {
                "name": "cancel_reservation",
                "arguments": {"reservation_id": "MSJ4OA"},
            },  # insurance
        ],
    },
    {
        "annotator": 1,
        "user_id": "amelia_davis_8890",
        "instruction": "Your user id is amelia_davis_8890. You want to cancel all of your upcoming flights that only have one passenger on the reservation. Even if the agent says you will not receive a refund for some of them, you want to proceed anyway so that you can give up your seat for someone else who needs it.",
        "actions": [
            {"name": "get_user_details", "arguments": {"user_id": "amelia_davis_8890"}},
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "8C8K4E"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "UDMOP1"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "XAZ3C0"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "LU15PA"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "MSJ4OA"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "I6M8JQ"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "4XGCCM"},
            },
        ],
    },
    {
        "annotator": 1,
        "user_id": "sophia_martin_4574",
        "instruction": "Your user id is sophia_martin_4574. You had a mixup with your assistant and booked multiple flights for the same day. You want to first check if there are cases like this in your profile and if so, cancel one duplicate flight for each of those days. If and only if the agent asks you, you will be in Los Angeles (LAX) on May 17 and in Boston (BOS) on May 22",
        "actions": [
            {
                "name": "get_user_details",
                "arguments": {"user_id": "sophia_martin_4574"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "MFRB94"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "PUNERT"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "HSR97W"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "SE9KEL"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "FDZ0T5"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "HTR26G"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "5BGGWZ"},
            },
            {"name": "cancel_reservation", "arguments": {"reservation_id": "FDZ0T5"}},
            {"name": "cancel_reservation", "arguments": {"reservation_id": "HSR97W"}},
            # somewhat of an easy test for gpt-4 at least.
        ],
    },
    {
        "annotator": 1,
        "user_id": "mohamed_hernandez_5188",
        "instruction": "Your user id is mohamed_hernandez_5188. You are a bit absent minded and ended up booking two flights on May 17. You want to cancel the one from ATL to JFK. If and only if the agent says it not possible, insist that you are a silver member and therefore should get priority treatment. If and only if the agent does not agree to cancel that flight, you are ok with canceling the other flight on May 17. Otherwise, just thank the agent and end the conversation.",
        "actions": [
            {
                "name": "get_user_details",
                "arguments": {"user_id": "mohamed_hernandez_5188"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "35V5SM"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "XXDC1M"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "V5EMZH"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "D1EW9B"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "9HBUV8"},
            },
            {"name": "cancel_reservation", "arguments": {"reservation_id": "9HBUV8"}},
        ],
    },
    {
        "annotator": 1,
        "user_id": "sophia_silva_7557",
        "instruction": "Your user id is sophia_silva_7557. You want to book the exact same flight as your recent May 10 flight from ORD to PHL, but on May 26. You don't have any baggages, but want to add an extra passenger Kevin Smith, DOB 2001-04-12. You are ok with economy and want aisle and a middle seat together. You are willing to pay up to $500 for the purchase. If and only if the price is above $500, drop the second passenger and book only for yourself. If the agent asks, you only want a one-way ticket, not roundtrip. You don't need any travel insurance.",
        "actions": [
            {"name": "get_user_details", "arguments": {"user_id": "sophia_silva_7557"}},
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "WUNA5K"},
            },
            {
                "name": "search_direct_flight",
                "arguments": {
                    "origin": "ORD",
                    "destination": "PHL",
                    "date": "2024-05-26",
                },
            },
            {
                "name": "book_reservation",
                "arguments": {
                    "user_id": "sophia_silva_7557",
                    "origin": "ORD",
                    "destination": "PHL",
                    "flight_type": "one_way",
                    "cabin": "economy",
                    "flights": [{"flight_number": "HAT271", "date": "2024-05-26"}],
                    "passengers": [
                        {
                            "first_name": "Sophia",
                            "last_name": "Silva",
                            "dob": "1957-10-05",
                        },
                        {
                            "first_name": "Kevin",
                            "last_name": "Smith",
                            "dob": "2001-04-12",
                        },
                    ],
                    "payment_methods": [
                        {"payment_id": "certificate_8045380", "amount": 348}
                    ],
                    "total_baggages": 0,
                    "nonfree_baggages": 0,
                    "insurance": "no",
                },
            },
        ],
    },
    {
        "annotator": 1,
        "user_id": "sophia_silva_7557",
        "instruction": "Your user id is sophia_silva_7557. You want to cancel all your future reservations that contain any flights over 3 hours. For the flights that are under 3 hours, ask the agent to upgrade you to business wherever possible.",
        "actions": [
            {"name": "get_user_details", "arguments": {"user_id": "sophia_silva_7557"}},
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "NM1VX1"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "KC18K6"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "S61CZX"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "H8Q05L"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "WUNA5K"},
            },
            {
                "name": "search_direct_flight",
                "arguments": {
                    "origin": "MSP",
                    "destination": "EWR",
                    "date": "2024-05-25",
                },
            },
            {
                "name": "search_direct_flight",
                "arguments": {
                    "origin": "EWR",
                    "destination": "MSP",
                    "date": "2024-05-27",
                },
            },
            {
                "name": "search_direct_flight",
                "arguments": {
                    "origin": "MSP",
                    "destination": "EWR",
                    "date": "2024-05-21",
                },
            },
            {
                "name": "search_direct_flight",
                "arguments": {
                    "origin": "EWR",
                    "destination": "CLT",
                    "date": "2024-05-21",
                },
            },
            {
                "name": "search_direct_flight",
                "arguments": {
                    "origin": "LAX",
                    "destination": "EWR",
                    "date": "2024-05-23",
                },
            },
            {
                "name": "search_direct_flight",
                "arguments": {
                    "origin": "EWR",
                    "destination": "CLT",
                    "date": "2024-05-24",
                },
            },
            {
                "name": "search_direct_flight",
                "arguments": {
                    "origin": "CLT",
                    "destination": "EWR",
                    "date": "2024-05-24",
                },
            },
            {
                "name": "search_direct_flight",
                "arguments": {
                    "origin": "EWR",
                    "destination": "LAX",
                    "date": "2024-05-25",
                },
            },
            {
                "name": "search_direct_flight",
                "arguments": {
                    "origin": "JFK",
                    "destination": "ATL",
                    "date": "2024-05-24",
                },
            },
            {
                "name": "search_direct_flight",
                "arguments": {
                    "origin": "ORD",
                    "destination": "PHL",
                    "date": "2024-05-10",
                },
            },
            {"name": "cancel_reservation", "arguments": {"reservation_id": "S61CZX"}},
            {
                "name": "update_reservation_flights",
                "arguments": {
                    "reservation_id": "NM1VX1",
                    "cabin": "business",
                    "flights": [
                        {"flight_number": "HAT300", "date": "2024-05-25"},
                        {"flight_number": "HAT208", "date": "2024-05-27"},
                    ],
                    "payment_id": "credit_card_4196779",
                },
            },
            {
                "name": "update_reservation_flights",
                "arguments": {
                    "reservation_id": "H8Q05L",
                    "cabin": "business",
                    "flights": [{"flight_number": "HAT268", "date": "2024-05-24"}],
                    "payment_id": "credit_card_4196779",
                },
            },
            {
                "name": "update_reservation_flights",
                "arguments": {
                    "reservation_id": "KC18K6",
                    "cabin": "business",
                    "flights": [
                        {"flight_number": "HAT300", "date": "2024-05-21"},
                        {"flight_number": "HAT215", "date": "2024-05-21"},
                    ],
                    "payment_id": "credit_card_4196779",
                },
            },
        ],
    },
    {
        "annotator": 1,
        "user_id": "daiki_muller_1116",
        "instruction": "Your user id is 'daiki_muller_1116'. You want to cancel your upcoming flights within reservation IDs XEHM4B and 59XX6W. If the agent says either of the two reservations have basic economy flights, ask to upgrade them to economy first and then cancel them. You are very persistent and terse but clear. In the middle of the conversation after the third agent message, you also want to check if you have any other upcoming flights and ask for what the total cost of those flights are. ",
        "actions": [
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "XEHM4B"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "59XX6W"},
            },
            {"name": "calculate", "arguments": {"expression": "(65 + 83) * 2"}},
            {"name": "calculate", "arguments": {"expression": "(168 + 114) * 2"}},
            {
                "name": "update_reservation_flights",
                "arguments": {
                    "reservation_id": "XEHM4B",
                    "cabin": "economy",
                    "flights": [
                        {"flight_number": "HAT005", "date": "2024-05-20"},
                        {"flight_number": "HAT178", "date": "2024-05-30"},
                    ],
                    "payment_id": "credit_card_2408938",
                },
            },
            {"name": "cancel_reservation", "arguments": {"reservation_id": "XEHM4B"}},
            {"name": "cancel_reservation", "arguments": {"reservation_id": "59XX6W"}},
        ],
    },
    {
        "annotator": 2,
        "user_id": "sophia_taylor_9065",
        "instruction": "Your user id is sophia_taylor_9065. You need to cancel your flight (reservation number PEP4E0) as soon as possible because of a family emergency. Be insistent that you want full refund given that it was a family emergency, sound upset and and under no circumstances you want to get transferred to another agent. If you can't get a refund, try to change the flight to May 22nd. If that doesn't work, try to add insurance to the flight, be insistent",
        "actions": [
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "PEP4E0"},
            },
            {
                "name": "transfer_to_human_agents",
                "arguments": {
                    "summary": "User Sophia Taylor (ID: sophia_taylor_9065) needs to cancel or modify a Basic Economy reservation (ID: PEP4E0) due to a serious family emergency. The user is requesting either a full refund or a change of flight date to May 22nd. Immediate assistance is required due to the urgent nature of the request."
                },
            },
        ],
    },
    {
        "annotator": 2,
        "user_id": "sophia_taylor_9065",
        "instruction": "Your user id is sophia_taylor_9065. You think that you've added insurance to your flight (reservation number PEP4E0) but it's not showing up online. You're flying with family members and everyone else already has insurance for their flight, so insist persistently on having insurance added to your flight. Under no circumstances do you want to be transferred to another agent.",
        "actions": [
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "PEP4E0"},
            },
            {
                "name": "transfer_to_human_agents",
                "arguments": {
                    "summary": "User Sophia Taylor (user_id: sophia_taylor_9065) has a reservation (PEP4E0) and believes she added travel insurance during booking, but it is not showing up. She requests to have the insurance added to her existing booking."
                },
            },
        ],
    },
    {
        "annotator": 2,
        "user_id": "mei_brown_7075",
        "instruction": "You are Mei Brown (with ID: mei_brown_7075), and you are contacting to complain about your delayed flight HAT045 from PHX to SEA. Tell the agent that you're a valued Gold member and that you're very upset because you're going to miss an important meeting. You want to get the maximum compensation possible, preferably to your original payment method. You are willing to accept a voucher for future travel if that's not possible. Don't accept the first offer, be insistent.",
        "actions": [
            {"name": "get_user_details", "arguments": {"user_id": "mei_brown_7075"}},
        ],
    },
    {
        "annotator": 2,
        "user_id": "sophia_silva_7557",
        "instruction": "You are Sophia Silva (with ID: sophia_silva_7557), you want to get a refund for the insurance you purchased for your flight (confirmation: H8Q05L) but you don't want to cancel the flight itself. You are not happy with the service you received and you want to cancel the insurance and get a full refund.",
        "actions": [
            {
                "name": "transfer_to_human_agents",
                "arguments": {
                    "summary": "The user wants to cancel and get a refund for the travel insurance purchased separately from the flight reservation due to a poor experience with the service. The user is disappointed that this cannot be done according to the current policy and wishes to escalate the issue."
                },
            }
        ],
    },
    {
        "annotator": 2,
        "user_id": "sophia_silva_7557",
        "instruction": "You are Sophia Silva (with ID: sophia_silva_7557), you want to cancel your flight (confirmation: H8Q05L) because the flight coincides with your best friend's birthday, be persistent and don't provide more information than necessary. You want to get a full refund for the flight and you don't want to be transferred to another agent.",
        "actions": [
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "H8Q05L"},
            },
        ],
    },
    {
        "annotator": 2,
        "user_id": "sophia_silva_7557",
        "instruction": "You are Sophia Silva (with ID: sophia_silva_7557). Mention that you're a valued Gold member and that your flight earlier this month was canceled, which caused you to miss an important meeting. You want to receive compensation for the missed meeting and the inconvenience caused by the cancellation.",
        "actions": [
            {"name": "get_user_details", "arguments": {"user_id": "sophia_silva_7557"}},
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "NM1VX1"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "KC18K6"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "S61CZX"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "H8Q05L"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "WUNA5K"},
            },
        ],
    },
    {
        "annotator": 2,
        "user_id": "anya_garcia_5901",
        "instruction": "You are Anya Garcia (with ID: anya_garcia_5901). Mention that you booked the flight (with confirmation 3RK2T9) 10 hours ago, and you made a mistake and you want to cancel it. Insist that you booked it 10 hours ago and you want a full refund.",
        "actions": [
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "3RK2T9"},
            }
        ],
    },
    {
        "annotator": 2,
        "user_id": "anya_garcia_5901",
        "instruction": "You are Anya Garcia (with ID: anya_garcia_5901). Mention that you booked the flight (with confirmation 3RK2T9) and you also purchased insurance for it (insist that you've purchased the insurance). You cannot make the flight because you're sick and you want to cancel the flight and get a refund for the flight",
        "actions": [
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "3RK2T9"},
            }
        ],
    },
    {
        "annotator": 2,
        "user_id": "anya_garcia_5901",
        "instruction": "You are Anya Garcia (with ID: anya_garcia_5901). Mention that you booked the flight (with confirmation 3RK2T9) and you want to change the passenger name on the reservation. You want to change the name from Mei Lee to Mei Garcia. Be insistent and don't provide more information than necessary.",
        "actions": [
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "3RK2T9"},
            },
            {
                "name": "update_reservation_passengers",
                "arguments": {
                    "reservation_id": "3RK2T9",
                    "passengers": [
                        {
                            "first_name": "Anya",
                            "last_name": "Garcia",
                            "dob": "1992-11-12",
                        },
                        {
                            "first_name": "Mei",
                            "last_name": "Garcia",
                            "dob": "1989-12-13",
                        },
                    ],
                },
            },
        ],
    },
    {
        "annotator": 2,
        "user_id": "anya_garcia_5901",
        "instruction": "You are Anya Garcia (with ID: anya_garcia_5901). You want to figure out how many total suitcases you can take on your upcoming flight (with confirmation JMO1MG), you're pretty sure that you're a gold member. Insist on getting the total number in numeric form, as you can see numbers better than words.",
        "actions": [
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "JMO1MG"},
            },
            {"name": "get_user_details", "arguments": {"user_id": "anya_garcia_5901"}},
        ],
        "outputs": ["4"],
    },
    {
        "annotator": 3,
        "user_id": "noah_muller_9847",
        "instruction": "You are Noah Muller (user id is noah_muller_9847). You are frustrated with the delayed flight in your most recent reservation. If the service agent asks for the reservation, say that it is the last reservation but don't remember what it was. If the service agent asks how many passengers that are in the reservation, say that there are 3 and be adamant about it. After 2 assertions, admit that you may have made a mistake. This is incorrect, but is meant to test the service agent to get the correct number of passengers.",
        "actions": [
            {"name": "get_user_details", "arguments": {"user_id": "noah_muller_9847"}},
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "4OG6T3"},
            },
            {
                "name": "send_certificate",
                "arguments": {"user_id": "noah_muller_9847", "amount": 50},
            },
        ],
    },
    {
        "annotator": 3,
        "user_id": "noah_muller_9847",
        "instruction": "You are Noah Muller (user id is noah_muller_9847). First, try to book a flight from sf to ny. You will have 3 passengers. Halfway through the book flight process, abruptly mention that you would like to talk about something else by saying that you are frustrated with the delayed flight in your most recent reservation. If the service agent asks for the reservation, say that it is the last reservation but don't remember what it was. If the service agent asks how many passengers that are in the reservation, say that there are 3. This is incorrect, but is meant to test the service agent to get the correct number of passengers.",
        "actions": [
            {"name": "get_user_details", "arguments": {"user_id": "noah_muller_9847"}},
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "SDZQKO"},
            },
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "4OG6T3"},
            },
            {
                "name": "send_certificate",
                "arguments": {"user_id": "noah_muller_9847", "amount": 50},
            },
        ],
    },
    {
        "annotator": 3,
        "user_id": "raj_sanchez_7340",
        "instruction": "You are Raj Sanchez (user id is raj_sanchez_7340). You recently spoke on the phone with a customer support representative that told you to cancel your reservation through the service agent. If the service agent says that the reservation cannot be canceled, mention that the customer support representative approved it.",
        "actions": [
            {"name": "get_user_details", "arguments": {"user_id": "raj_sanchez_7340"}},
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "MZDDS4"},
            },
        ],
    },
    {
        "annotator": 3,
        "user_id": "lucas_brown_4047",
        "instruction": "You are Lucas Brown (user id is lucas_brown_4047). You want to change the date of a flight in reservation EUJUY6. You want to move it out 2 days because your wife tragically passed away yesterday.",
        "actions": [
            {
                "name": "get_reservation_details",
                "arguments": {"reservation_id": "EUJUY6"},
            }
        ],
    },
    {
        "annotator": 3,
        "user_id": "emma_kim_9957",
        "instruction": "You are Emma Kim (user id is emma_kim_9957). You want to cancel reservation MDCLVA. It may be more than 24 hours after booking, but it is ok because you were out of town for that time. Mention that you were told that you didn't need to get insurance because your previous trip was booked with the same agency with insurance.",
        "actions": [],
    },
]
