<?php
// strip slashes before putting the form data into target file
$val = $_GET['val'];
//$cd="test";
// Show the msg, if the code string is empty
//if (empty($val))
  //  $val="0"

// if the code string is not empty then open the target file and put form data in it
    echo "PHP gestartet";
    $file = fopen("input.txt", "w");
    echo "Datei geöffnet";
    //echo fwrite($file, $cd);
  fwrite($file, $val);
    // show a success msg 
    echo "Wert " , $val , " erfolgreich geschrieben";
    fclose($file);

?>
