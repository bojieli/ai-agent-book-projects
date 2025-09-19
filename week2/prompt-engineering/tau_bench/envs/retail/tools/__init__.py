# Copyright Sierra

from .calculate import Calculate
from .cancel_pending_order import CancelPendingOrder
from .exchange_delivered_order_items import ExchangeDeliveredOrderItems
from .find_user_id_by_email import FindUserIdByEmail
from .find_user_id_by_name_zip import FindUserIdByNameZip
from .get_order_details import GetOrderDetails
from .get_product_details import GetProductDetails
from .get_user_details import GetUserDetails
from .list_all_product_types import ListAllProductTypes
from .modify_pending_order_address import ModifyPendingOrderAddress
from .modify_pending_order_items import ModifyPendingOrderItems
from .modify_pending_order_payment import ModifyPendingOrderPayment
from .modify_user_address import ModifyUserAddress
from .return_delivered_order_items import ReturnDeliveredOrderItems
from .think import Think
from .transfer_to_human_agents import TransferToHumanAgents


ALL_TOOLS = [
    Calculate,
    CancelPendingOrder,
    ExchangeDeliveredOrderItems,
    FindUserIdByEmail,
    FindUserIdByNameZip,
    GetOrderDetails,
    GetProductDetails,
    GetUserDetails,
    ListAllProductTypes,
    ModifyPendingOrderAddress,
    ModifyPendingOrderItems,
    ModifyPendingOrderPayment,
    ModifyUserAddress,
    ReturnDeliveredOrderItems,
    Think,
    TransferToHumanAgents,
]
