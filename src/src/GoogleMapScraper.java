package scrape;

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

        scraper.scrapeGoogleMapsDynamic(place);
    }

    private void scrapeGoogleMapsDynamic(String place) {
        // Auto-detect and install the correct ChromeDriver
        

        ChromeOptions options = new ChromeOptions();
        options.addArguments("--headless"); // Run in headless mode
        options.addArguments("--disable-blink-features=AutomationControlled");

        WebDriver driver = new ChromeDriver(options);
        String url = "https://www.google.com/maps/search/" + place.replace(" ", "+");
        driver.get(url);

        WebDriverWait wait = new WebDriverWait(driver, Duration.ofSeconds(10));

        try {
            // Extract Place Name
            WebElement placeNameElement = wait.until(ExpectedConditions.visibilityOfElementLocated(
                    By.xpath("//h1[contains(@class, 'DUwDvf')]")));
            String placeName = placeNameElement.getText();

            // Extract Address (Alternate XPaths in case Google changes the structure)
            WebElement addressElement = wait.until(ExpectedConditions.visibilityOfElementLocated(
                    By.xpath("//div[contains(@class, 'Io6YTe')] | //span[contains(@class, 'UsdlK')]")));
            String address = addressElement.getText();

            System.out.println("✅ Place Name: " + placeName);
            System.out.println("✅ Address: " + address);

        } catch (Exception e) {
            System.out.println("❌ Could not retrieve place details. Google may have changed its page structure.");
        } finally {
            driver.quit();
        }
    }
}
