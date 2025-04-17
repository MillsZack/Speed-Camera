import javax.swing.*;

public class SpeedCameraApp {
    public static void main(String[] args) {
        SwingUtilities.invokeLater(() -> {
            SpeedCameraFrame frame = new SpeedCameraFrame();
            frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
            frame.setVisible(true);
        });
    }
}
