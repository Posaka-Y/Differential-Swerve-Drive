/* 自作ユニット基板の一次生存確認用の最小ファーム。
 *
 * 目的は「MCUが起動してコードを実行している」ことを目視で確定させることだけ。
 * CAN・SPI・AMT22・Flash は一切触らないので、周辺回路の実装状態に依存しない。
 *
 * 依存を意図的に減らしてある:
 *   - クロックは reset 直後の HSI 16MHz のまま。水晶 Y1 が発振しなくても動く。
 *   - 点滅は LED_RUN = PA5 (R20 -> D8 緑)。NUCLEO の LD2 と同じピンなので、
 *     NUCLEO へ書いても同じ挙動になり、対照試験に使える。
 *
 * 点滅パターンは 200ms ON / 800ms OFF の非対称。電源やクロックの異常で
 * 意図せず高速点滅した場合と、正常動作とを目視で区別するため。
 */
#include "platform/clock.h"
#include "platform/gpio.h"

enum {
    BLINK_ON_MS = 200U,
    BLINK_OFF_MS = 800U,
};

int main(void)
{
    clock_init();
    board_io_init();

    for (;;) {
        status_led_write(true);
        clock_delay_ms(BLINK_ON_MS);
        status_led_write(false);
        clock_delay_ms(BLINK_OFF_MS);
    }
}
