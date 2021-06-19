import sys
from logger_tt import setup_logging, logger


def will_fail():
    loren_ipsum = "On the other hand, we denounce with righteous indignation and dislike men who are so beguiled and " \
                  "demoralized by the charms of pleasure of the moment, so blinded by desire, that they cannot " \
                  "foresee the pain and trouble that are bound to ensue; and equal blame belongs to those who fail in " \
                  "their duty through weakness of will, which is the same as saying through shrinking from toil and " \
                  "pain. These cases are perfectly simple and easy to distinguish. In a free hour, when our power of " \
                  "choice is untrammelled and when nothing prevents our being able to do what we like best, " \
                  "every pleasure is to be welcomed and every pain avoided. But in certain circumstances and owing to " \
                  "the claims of duty or the obligations of business it will frequently occur that pleasures have to " \
                  "be repudiated and annoyances accepted. The wise man therefore always holds in these matters to " \
                  "this principle of selection: he rejects pleasures to secure other greater pleasures, or else he " \
                  "endures pains to avoid worse pains. "

    raise RuntimeError(f'Below is the random text used as a standard to test font: \n{loren_ipsum}')


if __name__ == '__main__':
    limit_line_length = int(sys.argv[1])
    analyze_raise = bool(int(sys.argv[2]))
    setup_logging(limit_line_length=limit_line_length, analyze_raise_statement=analyze_raise)
    logger.info(sys.argv)
    will_fail()
