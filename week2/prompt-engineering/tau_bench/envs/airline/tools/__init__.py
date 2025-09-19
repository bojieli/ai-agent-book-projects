# Copyright Sierra

from .book_reservation import BookReservation
from .calculate import Calculate
from .cancel_reservation import CancelReservation
from .get_reservation_details import GetReservationDetails
from .get_user_details import GetUserDetails
from .list_all_airports import ListAllAirports
from .search_direct_flight import SearchDirectFlight
from .search_onestop_flight import SearchOnestopFlight
from .send_certificate import SendCertificate
from .think import Think
from .transfer_to_human_agents import TransferToHumanAgents
from .update_reservation_baggages import UpdateReservationBaggages
from .update_reservation_flights import UpdateReservationFlights
from .update_reservation_passengers import UpdateReservationPassengers

ALL_TOOLS = [
    BookReservation,
    Calculate,
    CancelReservation,
    GetReservationDetails,
    GetUserDetails,
    ListAllAirports,
    SearchDirectFlight,
    SearchOnestopFlight,
    SendCertificate,
    Think,
    TransferToHumanAgents,
    UpdateReservationBaggages,
    UpdateReservationFlights,
    UpdateReservationPassengers,
]
