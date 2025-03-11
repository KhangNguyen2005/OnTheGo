package scrape;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URLEncoder;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Scanner;

import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

public class GoogleMapScraper {

    public static void main(String[] args) {
        GoogleMapScraper scraper = new GoogleMapScraper();
        Scanner scanner = new Scanner(System.in);
        System.out.print("Enter the place, address, or GPS coordinates to scrape: ");
        String place = scanner.nextLine();
        scanner.close();

        try {
            scraper.scrapeGoogleMapsStatic(place);
            scraper.scrapeGoogleMapsDynamic(place);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    private String formatPlaceForUrl(String place) {
        place = place.trim();
        if (place.matches("-?\\d+(\\.\\d+)?,-?\\d+(\\.\\d+)?")) {
            return "https://www.google.com/maps/search/?api=1&query=" + place;
        } else {
            try {
                return "https://www.google.com/maps/search/" + URLEncoder.encode(place, StandardCharsets.UTF_8);
            } catch (Exception e) {
                System.out.println("Error encoding URL: " + e.getMessage());
                return null;
            }
        }
    }

    private void scrapeGoogleMapsStatic(String place) throws IOException {
        String url = formatPlaceForUrl(place);
        if (url == null) {
            System.out.println("Invalid URL format.");
            return;
        }

        HttpURLConnection connection = (HttpURLConnection) new URL(url).openConnection();
        connection.setRequestMethod("GET");
        connection.setRequestProperty("User-Agent", "Mozilla/5.0");

        int responseCode = connection.getResponseCode();
        if (responseCode == 200) {
            BufferedReader in = new BufferedReader(new InputStreamReader(connection.getInputStream()));
            String inputLine;
            StringBuilder content = new StringBuilder();
            while ((inputLine = in.readLine()) != null) {
                content.append(inputLine);
            }
            in.close();
            connection.disconnect();

            if (content.toString().contains("some-static-info")) {
                System.out.println("Found some static data!");
            } else {
                System.out.println("Could not extract static data.");
            }
        } else {
            System.out.println("Failed to retrieve page content. Response code: " + responseCode);
        }
    }

    private void scrapeGoogleMapsDynamic(String place) {
        System.setProperty("webdriver.chrome.driver", "path/to/chromedriver");

        ChromeOptions options = new ChromeOptions();
        options.addArguments("--headless"); // Run in headless mode
        options.addArguments("--disable-blink-features=AutomationControlled");

        WebDriver driver = new ChromeDriver(options);
        String url = formatPlaceForUrl(place);
        if (url == null) {
            System.out.println("Invalid URL format.");
            driver.quit();
            return;
        }

        driver.get(url);
        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));

        try {
            WebElement placeNameElement = wait.until(ExpectedConditions.visibilityOfElementLocated(By.xpath("//h1[contains(@class, 'header-title')]")));
            WebElement addressElement = wait.until(ExpectedConditions.visibilityOfElementLocated(By.xpath("//div[contains(@class, 'section-info-line')]//span")));

            String placeName = placeNameElement.getText();
            String address = addressElement.getText();

            System.out.println("Place Name: " + placeName);
            System.out.println("Address: " + address);
        } catch (Exception e) {
            System.out.println("Could not retrieve place details. The page structure may have changed.");
        } finally {
            driver.quit();
        }
    }
}
