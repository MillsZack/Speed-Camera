import javax.swing.*;
import javax.swing.border.TitledBorder;
import java.awt.*;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;

public class SpeedCameraFrame extends JFrame {
    private double speedLimit = 30.0;
    private double threshold = 5.0;
    private boolean isActive = false;
    private JLabel statusLabel;
    private JTextField speedLimitField;
    private JTextField thresholdField;
    private JTextArea alertArea;
    private JToggleButton toggleButton;

    public SpeedCameraFrame() {
        setTitle("Speed Camera Control System");
        setSize(500, 400);
        setLocationRelativeTo(null);

        createUI();
    }

    private void createUI() {
        // Main panel with border layout
        JPanel mainPanel = new JPanel(new BorderLayout(10, 10));
        mainPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 10, 10));

        // Create control panel
        JPanel controlPanel = createControlPanel();
        mainPanel.add(controlPanel, BorderLayout.NORTH);

        // Create alert area
        alertArea = new JTextArea();
        alertArea.setEditable(false);
        alertArea.setFont(new Font("Monospaced", Font.PLAIN, 12));
        JScrollPane scrollPane = new JScrollPane(alertArea);
        scrollPane.setBorder(BorderFactory.createTitledBorder("Alerts"));
        mainPanel.add(scrollPane, BorderLayout.CENTER);

        // Add test button (would be replaced with actual camera interface)
        JButton testButton = new JButton("Simulate Vehicle Detection");
        testButton.addActionListener(e -> simulateVehicleDetection());
        mainPanel.add(testButton, BorderLayout.SOUTH);

        add(mainPanel);
    }

    private JPanel createControlPanel() {
        JPanel panel = new JPanel(new GridLayout(0, 2, 10, 10));
        panel.setBorder(BorderFactory.createTitledBorder("Camera Settings"));

        // Speed limit input
        panel.add(new JLabel("Speed Limit (mph):"));
        speedLimitField = new JTextField(String.valueOf(speedLimit));
        panel.add(speedLimitField);

        // Threshold input
        panel.add(new JLabel("Alert Threshold (mph):"));
        thresholdField = new JTextField(String.valueOf(threshold));
        panel.add(thresholdField);

        // Status indicator
        panel.add(new JLabel("System Status:"));
        statusLabel = new JLabel("INACTIVE");
        statusLabel.setForeground(Color.RED);
        statusLabel.setFont(statusLabel.getFont().deriveFont(Font.BOLD));
        panel.add(statusLabel);

        // Toggle button
        toggleButton = new JToggleButton("Activate System");
        toggleButton.addActionListener(e -> toggleSystem());
        panel.add(toggleButton);

        return panel;
    }

    private void toggleSystem() {
        isActive = !isActive;

        if (isActive) {
            try {
                speedLimit = Double.parseDouble(speedLimitField.getText());
                threshold = Double.parseDouble(thresholdField.getText());
                statusLabel.setText("ACTIVE");
                statusLabel.setForeground(new Color(0, 150, 0)); // Dark green
                toggleButton.setText("Deactivate System");
                toggleButton.setBackground(new Color(144, 238, 144)); // Light green
                alertArea.append("System activated. Monitoring for speeds > " +
                        (speedLimit + threshold) + " mph\n");
            } catch (NumberFormatException ex) {
                alertArea.append("ERROR: Please enter valid numbers for speed limit and threshold\n");
                isActive = false;
                toggleButton.setSelected(false);
            }
        } else {
            statusLabel.setText("INACTIVE");
            statusLabel.setForeground(Color.RED);
            toggleButton.setText("Activate System");
            toggleButton.setBackground(null); // Reset to default
            alertArea.append("System deactivated\n");
        }
    }

    private void simulateVehicleDetection() {
        if (isActive) {
            double randomSpeed = speedLimit + (Math.random() * 20); // Random speed around limit
            if (randomSpeed > speedLimit + threshold) {
                String alert = String.format("ALERT! Vehicle detected at %.1f mph (Limit: %.1f mph)\n",
                        randomSpeed, speedLimit);
                alertArea.append(alert);
                // Here you would trigger your actual alert mechanism
            } else {
                alertArea.append(String.format("Vehicle detected at %.1f mph - no alert\n", randomSpeed));
            }
        } else {
            alertArea.append("System is inactive - cannot detect vehicles\n");
        }
    }

    // Method to connect with actual camera hardware
    public void processDetectedSpeed(double detectedSpeed) {
        if (isActive) {
            if (detectedSpeed > speedLimit + threshold) {
                String alert = String.format("ALERT! Vehicle detected at %.1f mph (Limit: %.1f mph)\n",
                        detectedSpeed, speedLimit);
                SwingUtilities.invokeLater(() -> {
                    alertArea.append(alert);
                });
                // Trigger alert mechanisms here
            }
        }
    }
}