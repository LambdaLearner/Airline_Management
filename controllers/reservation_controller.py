# Add the project root directory to sys.path
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from datetime import datetime
import mysql.connector


# Models representing the real-world entities
from models.flight import Flight
from models.flight_reservation import FlightReservation
# Modules handling the database-related operations
from repositories.flight_repository import FlightRepository
from repositories.reservation_repository import ReservationRepository



__all__ = ['ReservationController']
class ReservationController:
    def __init__(self):
        # Establish a database connection
        self.connection = mysql.connector.connect(
            host="localhost",
            user="",
            password="secret",
            database="flight"
        )

        self.flight_repo = FlightRepository()
        self.reservation_repo = ReservationRepository()


    # A helper function to create Flight objects out of database tuples
    def create_flight_object(self, flight_data):
        # Reorder tuple to match the Flight initializer
        reordered_flight_data = flight_data[1:] + (flight_data[0],)
        return Flight(*reordered_flight_data)
    

    def view_reservations(self, user):
        print("In the function View Reservations:")
        reservations = self.reservation_repo.get_reservations_by_user(user)
        if not reservations :
            print("No reservations found for you")
            return
        for reservation in reservations:
            print(reservation)

    

    def cancel_reservation(self, user):
        # Input the reservation number
        reservation_number = input("Please enter the reservation number you want to cancel: ")

        # Validate the input
        if not reservation_number:
            print("Reservation number is required to cancel a reservation.")
            return

        # Check if the user is authorized to cancel this reservation
        user_reservations = self.reservation_repo.get_reservations_by_user(user)

        if reservation_number not in user_reservations:
            print(f"User {user.username} is not authorized to cancel reservation {reservation_number}.")
            return

        # Call the repository layer to cancel the reservation
        try:
            self.reservation_repo.cancel_reservation(reservation_number)
            print(f"Reservation {reservation_number} has been successfully canceled.")
        except Exception as e:
            print(f"Error canceling reservation: {e}")

    

    def process_payment(self, user, price):
        # Dummy payment processing logic to simulate successful payment
        print(f"Processing payment for {user.username} for total price of: ${price}")
        return True

    

    def make_reservation(self, user, direct_flight=None, itinerary=None):
        print("Initiating reservation process...")
        num_seats = int(input("How many seats would you like to reserve?: "))

        # Check if it's a direct flight or itinerary reservation
        if direct_flight:
            available_seats = direct_flight.get_available_seats()
            if num_seats > available_seats:
                print(f"Sorry, only {available_seats} seats available for this flight.")
                return
            total_price = float(direct_flight.get_ticket_price()) * num_seats
            print(f"Total price for {num_seats} seat(s) is: ${total_price}")
            # print(f"Direct Flight: {direct_flight}")
            # Check seat availability for the direct flight

            self.reservation_repo.create_reservation(
                user=user,  # Assuming the User object has this method
                flight_no=direct_flight.get_flight_no(),
                seats=num_seats,
                creation_date=datetime.now(),
                payment_amount=total_price
            )
            print(f"Reservation for flight {direct_flight.get_flight_no()} made successfully.")

        elif itinerary:
            total_price = 0
            all_available = True

            # Check seat availability for all flights in the itinerary
            for flight in itinerary:
                available_seats = flight.get_available_seats()
                if num_seats > available_seats:
                    print(f"Sorry, only {available_seats} seats available for flight {flight.get_flight_no()}.")
                    all_available = False
                    break
                total_price += float(flight.get_ticket_price()) * num_seats

            if not all_available:
                return

            print(f"Total price for {num_seats} seat(s) across the itinerary is: ${total_price}")

            # Create reservations for the entire itinerary
            for flight in itinerary:
                self.reservation_repo.create_reservation(
                    user=user,
                    flight_no=flight.get_flight_no(),
                    seats=num_seats,
                    creation_date=datetime.now(),
                    payment_amount=float(flight.get_ticket_price()) * num_seats
                )
            print("Itinerary reservation made successfully.")


    def _find_cheapest_route(self, flights_or_itineraries, departure_airport, destination_airport):
        # Create a graph structure with costs
        graph = {}
        for item in flights_or_itineraries:
            if isinstance(item, tuple):  # It's a direct flight
                flight = self.create_flight_object(item)
                dep_airport = flight.get_dep_port()
                arr_airport = flight.get_arri_port()
                price = flight.get_ticket_price()

                if dep_airport not in graph:
                    graph[dep_airport] = []
                graph[dep_airport].append((arr_airport, price, flight))

            elif isinstance(item, list):  # It's an itinerary (list of flight tuples)
                itinerary = [self.create_flight_object(flight) for flight in item]
                dep_airport = itinerary[0].get_dep_port()
                arr_airport = itinerary[-1].get_arri_port()
                total_price = sum(float(flight.get_ticket_price()) for flight in itinerary)

                if dep_airport not in graph:
                    graph[dep_airport] = []
                graph[dep_airport].append((arr_airport, total_price, itinerary))

        # Implement Dijkstra's algorithm
        priority_queue = [(0, departure_airport, [])]  # (current cost, current airport, current route)
        visited = {}  # To track the lowest cost to each airport

        while priority_queue:
            current_cost, current_airport, route = heapq.heappop(priority_queue)

            # If we have reached the destination, return the route
            if current_airport == destination_airport:
                return route

            # If we already found a cheaper way to this airport, skip it
            if current_airport in visited and current_cost >= visited[current_airport]:
                continue

            # Mark this airport as visited with the current cheapest cost
            visited[current_airport] = current_cost

            # Explore neighbors (connected flights from current airport)
            for neighbor_airport, flight_price, flight_data in graph.get(current_airport, []):
                new_cost = current_cost + flight_price
                new_route = route + [flight_data]  # Update route with current flight(s)

                # Add this new option to the priority queue to explore
                heapq.heappush(priority_queue, (new_cost, neighbor_airport, new_route))

        # If no route found, return None
        return None



    def search_flights(self, user):
        print("Search Flights:")
        date = input("Date (YYYY-MM-DD): ")
        departure = input("Departure Airport: ")
        destination = input("Destination Airport: ")

        flights_or_itineraries = self.flight_repo.find_flights(date, departure, destination)

        # Variables to keep track of the shortest flights
        shortest_itinerary = None
        shortest_itinerary_distance = float('inf')
        shortest_direct_flight = None
        shortest_direct_flight_distance = float('inf')

        for option in flights_or_itineraries:
            if isinstance(option, list):
                # It's an itinerary with multiple flights
                itinerary_flights = [self.create_flight_object(flight_tuple) for flight_tuple in option]
                total_distance = sum(flight.get_distance_km() for flight in itinerary_flights)
                if total_distance < shortest_itinerary_distance:
                    shortest_itinerary = itinerary_flights
                    shortest_itinerary_distance = total_distance
            else:
                # It's a direct flight
                flight_obj = self.create_flight_object(option)
                if flight_obj.get_distance_km() < shortest_direct_flight_distance:
                    shortest_direct_flight = flight_obj
                    shortest_direct_flight_distance = flight_obj.get_distance_km()

        # Output results
        if shortest_itinerary:
            print("\n\nShortest Itinerary found:")
            total_price = 0
            for flight in shortest_itinerary:
                price = flight.get_ticket_price()
                if price:
                    total_price += float(price)
                    print(flight)
                    print(price, "$")
            print(f"Total ticket price for the itinerary: {total_price} \n")
        else:
            print("No itineraries found.")

        if shortest_direct_flight:
            print(f"\n\nShortest Direct Flight: {shortest_direct_flight}")
            print(f"Ticket price: ", shortest_direct_flight.get_ticket_price(), "$")
        else:
            print("No direct flights found. \n")

        cheapest_option = self._find_cheapest_route(flights_or_itineraries, departure, destination)

        # Display the result
        if cheapest_option:
            print("Cheapest flight or itinerary found:")
            for flight in cheapest_option:
                print(flight)
        else:
            print("No available flights or itineraries found.")
        
        self._handle_user_choice(user, shortest_itinerary, shortest_direct_flight, cheapest_option)



    def _handle_user_choice(self, user, shortest_itinerary, shortest_direct_flight, cheapest_option):
        # Present options to the user for reservation
        print("\nOptions for reservation:")
        if shortest_itinerary:
            print("1. Shortest Itinerary")
        if shortest_direct_flight:
            print("2. Shortest Direct Flight")
        if cheapest_option:
            print("3. Cheapest Option")

        choice = input("Enter the number of your choice (1/2/3): ")

        # Call make_reservation based on user choice
        if choice == "1" and shortest_itinerary:
            self.make_reservation(user, itinerary=shortest_itinerary)
        elif choice == "2" and shortest_direct_flight:
            self.make_reservation(user, direct_flight=shortest_direct_flight)
        elif choice == "3" and cheapest_option:
            self.make_reservation(user, itinerary=cheapest_option)
        else:
            print("Invalid choice or option not available.")


