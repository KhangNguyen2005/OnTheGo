import org.jsoup.Jsoup;
import org.jsoup.nodes.Document;
import org.jsoup.nodes.Element;
import org.jsoup.select.Elements;

import java.io.IOException;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.Scanner;

public class KayakFlightScraper {

    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);

        System.out.print("Enter origin city: ");
        String origin = scanner.nextLine();

        System.out.print("Enter destination city: ");
        String destination = scanner.nextLine();

        System.out.print("Enter departure date (YYYY-MM-DD): ");
        String departureDate = scanner.nextLine();

        System.out.print("Enter return date (YYYY-MM-DD, or leave blank for one-way): ");
        String returnDate = scanner.nextLine();

        System.out.print("Enter number of passengers: ");
        String passengers = scanner.nextLine();

        try {
            String url = buildKayakUrl(origin, destination, departureDate, returnDate, passengers);
            Document doc = Jsoup.connect(url).userAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3").get();
            parseFlightResults(doc);

        } catch (IOException e) {
            System.err.println("Error fetching data: " + e.getMessage());
            e.printStackTrace();
        }
    }

    private static String buildKayakUrl(String origin, String destination, String departureDate, String returnDate, String passengers) throws IOException {
        String baseUrl = "https://www.kayak.com/flights/";
        String encodedOrigin = URLEncoder.encode(origin, StandardCharsets.UTF_8);
        String encodedDestination = URLEncoder.encode(destination, StandardCharsets.UTF_8);
        String url;

        if (returnDate.isEmpty()) {
            url = baseUrl + encodedOrigin + "-" + encodedDestination + "/" + departureDate + "?fs=stops=0;cabin=economy;bags=0;sort=bestflight_a";
        } else {
            url = baseUrl + encodedOrigin + "-" + encodedDestination + "/" + departureDate + "/" + returnDate + "?fs=stops=0;cabin=economy;bags=0;sort=bestflight_a";
        }

        url += "&adults=" + passengers;

        return url;
    }

    private static void parseFlightResults(Document doc) {
        Elements flightItems = doc.select("div[data-resultid]");

        if (flightItems.isEmpty()) {
            System.out.println("No flights found.");
            return;
        }

        for (Element flightItem : flightItems) {
            try {
                // Extract relevant information. This will vary depending on Kayak's HTML structure
                String airline = flightItem.select("div[class^='codeshares-airline-']").text();
                String departureTime = flightItem.select("span[class^='depart-time']").text();
                String arrivalTime = flightItem.select("span[class^='arrival-time']").text();
                String duration = flightItem.select("div[class^='duration-time']").text();
                String price = flightItem.select("span[class^='price-text']").text();
                String stops = flightItem.select("span[class^='stops-text']").text();

                System.out.println("Airline: " + airline);
                System.out.println("Departure: " + departureTime);
                System.out.println("Arrival: " + arrivalTime);
                System.out.println("Duration: " + duration);
                System.out.println("Price: " + price);
                System.out.println("Stops: " + stops);
                System.out.println("--------------------");
            } catch (Exception e) {
                System.err.println("Error parsing flight item: " + e.getMessage());
            }
        }
    }
}