package src;

import java.io.IOException;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.util.Scanner;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import org.openqa.selenium.By;
import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;
import org.openqa.selenium.support.ui.ExpectedConditions;
import org.openqa.selenium.support.ui.WebDriverWait;

public class GoogleMapScraper {

    private final OkHttpClient client = new OkHttpClient(); // OkHttpClient instance (OkHttp 4.11.0)

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

        Request request = new Request.Builder().url(url).build();
        Response response = client.newCall(request).execute();

        if (response.body() != null) {
            String htmlContent = response.body().string();
            response.close();

            if (htmlContent.contains("some-static-info")) {
                System.out.println("Found some static data!");
            } else {
                System.out.println("Could not extract static data.");
            }
        } else {
            System.out.println("Failed to retrieve page content.");
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
