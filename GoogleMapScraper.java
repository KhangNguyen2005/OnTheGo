package scrape;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.By;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

import java.io.IOException;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Scanner;

public class GoogleMapScraper {
    public static void main(String[] args) {
        GoogleMapScraper scraper = new GoogleMapScraper();

        // Get user input
        Scanner scanner = new Scanner(System.in);
        System.out.print("Enter the place, address, or GPS coordinates to scrape: ");
        String place = scanner.nextLine();

        try {
            // Scraping with OkHttpClient (for static content)
            scraper.scrapeGoogleMapsStatic(place);

            // Scraping with Selenium (for dynamic content)
            scraper.scrapeGoogleMapsDynamic(place);
        } catch (IOException e) {
            e.printStackTrace();
        }
    }

    // Method for formatting the input for a Google Maps search URL
    private String formatPlaceForUrl(String place) {
        place = place.trim();
        if (place.matches("-?\\d+(\\.\\d+)?,-?\\d+(\\.\\d+)?")) { // Detects GPS coordinates (latitude, longitude)
            return "https://www.google.com/maps/search/?api=1&query=" + place;
        } else {
            return "https://www.google.com/maps/search/" + URLEncoder.encode(place, StandardCharsets.UTF_8);
        }
    }

    // Method for scraping static content (this may not work for Google Maps but shows the concept)
    private void scrapeGoogleMapsStatic(String place) throws IOException {
        OkHttpClient client = new OkHttpClient();
        String url = formatPlaceForUrl(place);

        Request request = new Request.Builder()
                .url(url)
                .build();

        Response response = client.newCall(request).execute();
        String htmlContent = response.body().string();

        // Parse the content (this part will be specific to the website's structure)
        if (htmlContent.contains("some-static-info")) {
            System.out.println("Found some static data!");
            // Example: extract static info (address, name, etc.)
        } else {
            System.out.println("Could not extract static data.");
        }
    }

    // Method for scraping dynamic content (using Selenium and ChromeDriver)
    private void scrapeGoogleMapsDynamic(String place) {
        // Setup Selenium WebDriver with headless Chrome
        System.setProperty("webdriver.chrome.driver", "path/to/chromedriver");
        ChromeOptions options = new ChromeOptions();
        options.addArguments("--headless"); // Run in headless mode to avoid opening a browser window
        options.addArguments("--disable-blink-features=AutomationControlled"); // Avoid detection

        WebDriver driver = new ChromeDriver(options);
        String url = formatPlaceForUrl(place);
        driver.get(url);

        // Wait for the page to load completely
        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));

        try {
            // Example of extracting data (you would need to adjust this for actual data)
            WebElement placeNameElement = wait.until(ExpectedConditions.visibilityOfElementLocated(
                    By.xpath("//h1[contains(@class, 'header-title')]")
            ));
            WebElement addressElement = wait.until(ExpectedConditions.visibilityOfElementLocated(
                    By.xpath("//div[contains(@class, 'section-info-line')]//span")
            ));

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
